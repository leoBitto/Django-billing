from django import forms
from .models.base import Discount, Invoice, InvoiceLine
from django.core.exceptions import ValidationError
import os


class DiscountForm(forms.ModelForm):
    """Form per gestire gli sconti applicabili alle righe fattura"""
    class Meta:
        model = Discount
        fields = ['percentage', 'description']
        widgets = {
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Percentuale di sconto'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrizione dello sconto'
            }),
        }


class InvoiceForm(forms.ModelForm):
    """Form per la gestione delle fatture"""
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'invoice_type', 'issue_date', 
            'currency', 'issuer', 'receiver', 
            'taxable_amount', 'vat_amount', 'total_amount', 
            'payment_status', 'notes'
        ]

        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numero Fattura'
            }),
            'invoice_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'EUR'
            }),
            'issuer': forms.Select(attrs={
                'class': 'form-select'
            }),
            'receiver': forms.Select(attrs={
                'class': 'form-select'
            }),
            'taxable_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'vat_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Note aggiuntive'
            }),
        }


class InvoiceLineForm(forms.ModelForm):
    """Form per la gestione delle singole righe della fattura"""
    class Meta:
        model = InvoiceLine
        fields = [
            'invoice', 'line_number', 'product', 'external_product_code',
            'description', 'quantity', 'unit_of_measure', 'unit_price',
            'vat_rate', 'line_total', 'discount'
        ]
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'form-select'
            }),
            'line_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'product': forms.Select(attrs={
                'class': 'form-select'
            }),
            'external_product_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Codice prodotto fornitore'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descrizione del prodotto'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Es. pezzi, kg, metri'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'vat_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'line_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'discount': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class InvoiceUploadForm(forms.Form):
    xml_files = forms.FileField(
        widget=MultipleFileInput(),
        label='File XML Fatture',
        help_text='Seleziona uno o più file XML da caricare'
    )
    
    def clean_xml_files(self):
        xml_files = self.files.getlist('xml_files')
        if xml_files:
            valid_files = []
            for xml_file in xml_files:
                # Controlla l'estensione del file
                if not xml_file.name.endswith('.xml'):
                    raise forms.ValidationError("Il file caricato non è un file XML valido.")
                valid_files.append(xml_file)
            return valid_files
        else:
            raise forms.ValidationError("Nessun file XML caricato.")

