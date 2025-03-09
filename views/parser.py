from django.shortcuts import render, redirect
from django.views import View
from billing.forms import InvoiceUploadForm
from billing.models.base import Invoice, InvoiceLine, Discount
from warehouse.models.base import *
from crm.models.base import Company as CRMCompany
from decimal import Decimal
from xml.etree import ElementTree as ET

class InvoiceUploadView(View):
    template_name = 'billing/invoice_upload.html'

    def get(self, request):
        form = InvoiceUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = InvoiceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            xml_file = form.cleaned_data['xml_file']

            try:
                # Parsing del file XML
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Estrazione dei dati principali della fattura
                invoice_data = self.extract_invoice_data(root)

                # Creazione dell'oggetto Invoice
                invoice = Invoice.objects.create(
                    file_xml=xml_file,
                    invoice_number=invoice_data['invoice_number'],
                    invoice_type=invoice_data['invoice_type'],
                    issue_date=invoice_data['issue_date'],
                    currency=invoice_data['currency'],
                    issuer=self.get_or_create_company(invoice_data['issuer']),
                    receiver=self.get_or_create_company(invoice_data['receiver']),
                    taxable_amount=invoice_data['taxable_amount'],
                    vat_amount=invoice_data['vat_amount'],
                    total_amount=invoice_data['total_amount'],
                    notes=invoice_data.get('notes', '')
                )

                # Creazione delle righe della fattura
                for line_data in invoice_data['lines']:
                    product = self.get_or_create_product(line_data['product'])
                    discount = self.get_or_create_discount(line_data.get('discount'))

                    InvoiceLine.objects.create(
                        invoice=invoice,
                        line_number=line_data['line_number'],
                        product=product,
                        external_product_code=line_data['external_product_code'],
                        description=line_data['description'],
                        quantity=line_data['quantity'],
                        unit_of_measure=line_data['unit_of_measure'],
                        unit_price=line_data['unit_price'],
                        vat_rate=line_data['vat_rate'],
                        line_total=line_data['line_total'],
                        discount=discount
                    )

                return redirect('invoice_detail', pk=invoice.pk)

            except Exception as e:
                return render(request, self.template_name, {'form': form, 'error': f'Errore nel parsing del file XML: {e}'})

        else:
            return render(request, self.template_name, {'form': form, 'error': 'Errore nel caricamento del file.'})

    def extract_invoice_data(self, root):
        # Estrazione dei dati principali della fattura
        invoice_number = root.findtext('.//Numero')
        invoice_type = 'IN' if root.findtext('.//TipoDocumento') == 'TD01' else 'OUT'
        issue_date = root.findtext('.//Data')
        currency = root.findtext('.//Divisa')
        total_amount = Decimal(root.findtext('.//ImportoTotaleDocumento'))

        # Estrazione dei dati del cedente e del cessionario
        issuer_data = {
            'name': root.findtext('.//CedentePrestatore/DatiAnagrafici/Anagrafica/Denominazione'),
            'vat_number': root.findtext('.//CedentePrestatore/DatiAnagrafici/IdFiscaleIVA/IdCodice'),
            'address': root.findtext('.//CedentePrestatore/Sede/Indirizzo'),
            'city': root.findtext('.//CedentePrestatore/Sede/Comune'),
            'postal_code': root.findtext('.//CedentePrestatore/Sede/CAP'),
            'country': root.findtext('.//CedentePrestatore/Sede/Nazione'),
        }

        receiver_data = {
            'name': root.findtext('.//CessionarioCommittente/DatiAnagrafici/Anagrafica/Denominazione'),
            'vat_number': root.findtext('.//CessionarioCommittente/DatiAnagrafici/IdFiscaleIVA/IdCodice'),
            'address': root.findtext('.//CessionarioCommittente/Sede/Indirizzo'),
            'city': root.findtext('.//CessionarioCommittente/Sede/Comune'),
            'postal_code': root.findtext('.//CessionarioCommittente/Sede/CAP'),
            'country': root.findtext('.//CessionarioCommittente/Sede/Nazione'),
        }

        # Estrazione delle righe della fattura
        lines = []
        for line in root.findall('.//DettaglioLinee'):
            line_data = {
                'line_number': int(line.findtext('NumeroLinea')),
                'product': {
                    'name': line.findtext('Descrizione'),
                    'external_code': '',  # Aggiungi logica per ottenere il codice prodotto fornitore
                },
                'external_product_code': '',  # Aggiungi logica per ottenere il codice prodotto fornitore
                'description': line.findtext('Descrizione'),
                'quantity': Decimal(line.findtext('Quantita')),
                'unit_of_measure': line.findtext('UnitaMisura'),
                'unit_price': Decimal(line.findtext('PrezzoUnitario')),
                'vat_rate': Decimal(line.findtext('AliquotaIVA')),
                'line_total': Decimal(line.findtext('PrezzoTotale')),
                'discount': None,  # Aggiungi logica per ottenere lo sconto
            }
            lines.append(line_data)

        # Calcolo degli importi
        taxable_amount = sum(Decimal(line.findtext('PrezzoTotale')) for line in root.findall('.//DettaglioLinee'))
        vat_amount = total_amount - taxable_amount

        return {
            'invoice_number': invoice_number,
            'invoice_type': invoice_type,
            'issue_date': issue_date,
            'currency': currency,
            'issuer': issuer_data,
            'receiver': receiver_data,
            'taxable_amount': taxable_amount,
            'vat_amount': vat_amount,
            'total_amount': total_amount,
            'lines': lines,
        }

    def get_or_create_company(self, company_data):
        company, created = CRMCompany.objects.get_or_create(
            name=company_data['name'],
            defaults={
                'address': company_data['address'],
                'city': company_data['city'],
                'postal_code': company_data['postal_code'],
                'country': company_data['country'],
                'vat_number': company_data['vat_number'],
            }
        )
        return company

    def get_or_create_product(product_data, supplier):
        # Prima cerchiamo il prodotto tramite nome esatto
        product = Product.objects.filter(name=product_data['name']).first()
        
        # Se non trovato, cerchiamo negli alias
        if not product:
            alias = ProductAlias.objects.filter(alias_name=product_data['name'], supplier=supplier).first()
            if alias:
                product = alias.product
        
        # Se ancora non trovato, creiamo un nuovo prodotto
        if not product:
            product = Product.objects.create(
                name=product_data['name'],
                description=product_data.get('description', ''),
                external_code=product_data.get('external_code', '')
            )
            # Creiamo anche un alias associato al fornitore
            ProductAlias.objects.create(
                product=product,
                supplier=supplier,
                alias_name=product_data['name'],
                external_code=product_data.get('external_code', ''),
                description=product_data.get('description', '')
            )
        
        return product

    def get_or_create_discount(self, discount_data):
        if discount_data:
            discount, created = Discount.objects.get_or_create(
                percentage=discount_data['percentage'],
                defaults={'description': discount_data['description']}
            )
            return discount
        return None
