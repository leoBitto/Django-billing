from django import forms
from .models import Invoice, InvoiceLineItem
from django.forms.models import inlineformset_factory

class InvoiceEntryForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'issue_date', 'supplier', 'total_amount', 'vat', 'payment_due', 'notes']  # Correzione su "payment_due"
        labels = {
            'invoice_number': 'Numero Fattura',
            'issue_date': 'Data di Emissione',
            'supplier': 'Fornitore',
            'total_amount': 'Importo Totale',
            'vat': 'IVA',
            'payment_due': 'Data di Scadenza',
            'notes': 'Note',
        }
        widgets = {
            'supplier': forms.Select(attrs={'disabled': 'true'}),  # Fornitore precompilato
        }

InvoiceEntryInlineFormSet = inlineformset_factory(
    Invoice, InvoiceLineItem, form=InvoiceEntryForm,
    fields=['product', 'description', 'quantity', 'unit_price', 'discount_percentage', 'line_total'],  # Aggiunta di 'discount_percentage'
    extra=1,
    can_delete=True,
    labels={
        'product': 'Prodotto',
        'description': 'Descrizione',
        'quantity': 'Quantità',
        'unit_price': 'Prezzo Unitario',
        'discount_percentage': 'Sconto (%)',  # Nuovo campo
        'line_total': 'Totale Linea',
    }
)


class InvoiceExitForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'issue_date', 'customer', 'total_amount', 'vat', 'payment_due', 'notes']
        labels = {
            'invoice_number': 'Numero Fattura',
            'issue_date': 'Data di Emissione',
            'customer': 'Cliente',
            'total_amount': 'Importo Totale',
            'vat': 'IVA',
            'payment_due': 'Data di Scadenza',
            'notes': 'Note',
        }
        widgets = {
            'customer': forms.Select(attrs={'disabled': 'true'}),  # Cliente precompilato
        }

InvoiceExitInlineFormSet = inlineformset_factory(
    Invoice, InvoiceLineItem, form=InvoiceExitForm,
    fields=['product', 'description', 'quantity', 'unit_price', 'discount_percentage', 'line_total'],  # Aggiunta di 'discount_percentage'
    extra=1,
    can_delete=True,
    labels={
        'product': 'Prodotto',
        'description': 'Descrizione',
        'quantity': 'Quantità',
        'unit_price': 'Prezzo Unitario',
        'discount_percentage': 'Sconto (%)',  # Nuovo campo
        'line_total': 'Totale Linea',
    }
)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'payment_date', 'amount', 'method', 'iban', 'notes']  # Aggiunta di 'iban'
        labels = {
            'invoice': 'Fattura',
            'payment_date': 'Data di Pagamento',
            'amount': 'Importo Pagato',
            'method': 'Metodo di Pagamento',
            'iban': 'IBAN',  # Nuovo campo
            'notes': 'Note',
        }


class InvoiceUploadForm(forms.Form):
    file = forms.FileField(label="Carica Fattura (PDF)")