from django.db import models
from crm.models import Supplier, Customer
from decimal import Decimal
from warehouse.models.base import Product

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=50)  # Formato YYYY-XXX
    issue_date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_supplied')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_received')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.DecimalField(max_digits=10, decimal_places=2)
    payment_due = models.DateField(null=True, blank=True)  # Data di scadenza pagamento
    payment_date = models.DateField(null=True, blank=True)  # Data effettiva del pagamento
    notes = models.TextField(blank=True)  # Note addizionali sulla fattura
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.issue_date}"

    @property
    def invoice_type(self):
        # Identifichiamo se l'azienda è coinvolta come supplier o customer
        own_company = Company.objects.filter(is_own_company=True).first()

        if not own_company:
            return "Sconosciuto"  # Gestione fallback nel caso non ci sia un'azienda definita

        # Se il supplier è la propria azienda, è una fattura di vendita (attiva)
        if self.supplier and self.supplier.company == own_company:
            return "Vendita"  # Fattura attiva
        
        # Se il customer è la propria azienda, è una fattura di acquisto (passiva)
        if self.customer and self.customer.company == own_company:
            return "Acquisto"  # Fattura passiva
        
        return "Sconosciuto"

    @property
    def status(self):
        # Logica per calcolare lo stato della fattura in base alle date
        if self.payment_date:
            return "Pagata"
        elif self.payment_due and self.payment_due < date.today():
            return "Scaduta"
        return "In attesa di pagamento"
  

class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='line_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='invoice_lines', verbose_name=_("prodotto"))
    description = models.CharField(_("descrizione"), max_length=255, blank=True, null=True)  # optional in case product description is missing
    quantity = models.PositiveIntegerField(_("quantità"), default=1)
    unit_price = models.DecimalField(_("prezzo unitario"), max_digits=10, decimal_places=2)
    
    # Nuovi campi per la gestione degli sconti
    discount_percentage = models.DecimalField(_("percentuale di sconto"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    discounted_total = models.DecimalField(_("totale scontato"), max_digits=10, decimal_places=2, editable=False)
    
    vat_rate = models.DecimalField(_("aliquota IVA"), max_digits=5, decimal_places=2, default=Decimal('22.00'))  # default VAT rate
    line_total = models.DecimalField(_("totale riga"), max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Calcolo del totale della riga con sconto e IVA
        total_before_discount = self.unit_price * self.quantity
        discount_amount = total_before_discount * (self.discount_percentage / 100)
        self.discounted_total = total_before_discount - discount_amount
        self.line_total = self.discounted_total * (1 + self.vat_rate / 100)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("voce fattura")
        verbose_name_plural = _("voci fattura")

    def __str__(self):
        return f"{self.product.name} - {self.quantity} x {self.unit_price}"

class Payment(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(_("importo"), max_digits=10, decimal_places=2)
    payment_date = models.DateField(_("data di pagamento"))
    method = models.CharField(_("metodo di pagamento"), max_length=50)  # es. bonifico, carta di credito
    iban = models.CharField(_("IBAN"), max_length=34, blank=True, null=True)
    notes = models.TextField(_("note"), blank=True, null=True)

    class Meta:
        verbose_name = _("pagamento")
        verbose_name_plural = _("pagamenti")

    def __str__(self):
        return f"Pagamento di {self.amount} per {self.invoice.invoice_number}"

