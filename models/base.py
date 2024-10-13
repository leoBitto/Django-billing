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
        # Logica per distinguere tra fattura di entrata e di uscita
        if self.supplier and self.customer:
            return "Fattura ibrida"  # Casistica speciale, entrambi presenti
        elif self.supplier:
            return "Vendita"  # Fattura di vendita
        elif self.customer:
            return "Acquisto"  # Fattura di acquisto
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
    vat_rate = models.DecimalField(_("aliquota IVA"), max_digits=5, decimal_places=2, default=Decimal('22.00'))  # default VAT rate
    line_total = models.DecimalField(_("totale riga"), max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Calcola il totale della riga
        self.line_total = (self.unit_price * self.quantity) * (1 + self.vat_rate / 100)
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
    notes = models.TextField(_("note"), blank=True, null=True)

    class Meta:
        verbose_name = _("pagamento")
        verbose_name_plural = _("pagamenti")

    def __str__(self):
        return f"Pagamento di {self.amount} per {self.invoice.invoice_number}"

