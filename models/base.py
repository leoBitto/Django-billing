from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from decimal import Decimal

# Lazy loading dei modelli da altre app
if 'crm' in settings.INSTALLED_APPS:
    from crm.models.base import Company
else:
    Company = None

if 'warehouse' in settings.INSTALLED_APPS:
    from warehouse.models.base import Product
else:
    Product = None


class Discount(models.Model):
    """Modello per gestire gli sconti applicabili alle righe fattura"""
    percentage = models.DecimalField(
        _("percentuale di sconto"), 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    description = models.CharField(
        _("descrizione"), 
        max_length=255, 
        blank=True, 
        null=True
    )

    class Meta:
        verbose_name = _("sconto")
        verbose_name_plural = _("sconti")

    def __str__(self):
        return f"{self.percentage}% - {self.description or 'Sconto'}"


class Invoice(models.Model):
    """Modello principale per le fatture"""
    INVOICE_TYPES = [
        ('IN', _('Fattura di Acquisto')),
        ('OUT', _('Fattura di Vendita')),
    ]

    # File originale
    file_xml = models.FileField(upload_to='fatture_xml/',  blank=True, null=True, verbose_name=_("file XML"))
    

    # Dati principali della fattura
    invoice_number = models.CharField(_("numero fattura"), max_length=50, db_index=True)
    invoice_type = models.CharField(_("tipo fattura"), max_length=3, choices=INVOICE_TYPES)
    issue_date = models.DateField(_("data emissione"))
    currency = models.CharField(_("valuta"), max_length=3, default='EUR')
    
    # Collegamenti alle parti
    issuer = models.ForeignKey(
        'crm.Company', 
        on_delete=models.PROTECT, 
        related_name='invoices_issued',
        verbose_name=_("emittente")
    )
    receiver = models.ForeignKey(
        'crm.Company', 
        on_delete=models.PROTECT, 
        related_name='invoices_received',
        verbose_name=_("destinatario")
    )
    
    # Importi
    taxable_amount = models.DecimalField(_("imponibile"), max_digits=10, decimal_places=2)
    vat_amount = models.DecimalField(_("importo IVA"), max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(_("totale documento"), max_digits=10, decimal_places=2)
    
    # Metadati
    notes = models.TextField(_("note"), blank=True)
    created_at = models.DateTimeField(_("data creazione"), auto_now_add=True)
    updated_at = models.DateTimeField(_("ultima modifica"), auto_now=True)

    class Meta:
        verbose_name = _("fattura")
        verbose_name_plural = _("fatture")
        indexes = [
            models.Index(fields=['invoice_number', 'issue_date']),
        ]

    def __str__(self):
        return f"Fattura {self.invoice_number} del {self.issue_date}"


class InvoiceLine(models.Model):
    """Modello per le singole righe della fattura"""
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='invoice_lines',
        verbose_name=_("fattura")
    )
    line_number = models.IntegerField(_("numero riga"))
    
    # Dati prodotto
    product = models.ForeignKey(
        'warehouse.Product', 
        on_delete=models.PROTECT,
        verbose_name=_("prodotto")
    )
    external_product_code = models.CharField(
        _("codice prodotto fornitore"), 
        max_length=50, 
        blank=True,
        help_text=_("Codice del prodotto utilizzato dal fornitore")
    )
    description = models.TextField(
        _("descrizione"),
        help_text=_("Descrizione del prodotto come appare in fattura")
    )
    
    # Quantità e prezzi
    quantity = models.DecimalField(_("quantità"), max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(_("unità di misura"), max_length=10)
    unit_price = models.DecimalField(_("prezzo unitario"), max_digits=10, decimal_places=8)
    vat_rate = models.DecimalField(_("aliquota IVA"), max_digits=5, decimal_places=2)
    line_total = models.DecimalField(_("totale riga"), max_digits=10, decimal_places=2)
    
    # Sconto
    discount = models.ForeignKey(
        Discount, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("sconto")
    )

    class Meta:
        verbose_name = _("riga fattura")
        verbose_name_plural = _("righe fattura")
        ordering = ['line_number']
        indexes = [
            models.Index(fields=['invoice', 'product']),
        ]

    def __str__(self):
        return f"Riga {self.line_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        """
        Override del save per gestire l'aggiornamento del magazzino.
        Quando una riga viene salvata, aggiorna la quantità del prodotto
        in magazzino in base al tipo di fattura.
        """
        super().save(*args, **kwargs)
        
        # Aggiorna le quantità di magazzino
        delta = self.quantity if self.invoice.invoice_type == 'IN' else -self.quantity
        self.product.update_stock(delta)