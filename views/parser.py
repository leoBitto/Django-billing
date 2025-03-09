from django.shortcuts import render, redirect
from django.views import View
from billing.forms import InvoiceUploadForm
from billing.models.base import Invoice, InvoiceLine, Discount
from warehouse.models.base import Product, ProductAlias
from crm.models.base import Company as CRMCompany
from decimal import Decimal
from xml.etree import ElementTree as ET
import datetime
from django.contrib import messages

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
                
                # Gestione dei namespace nell'XML
                ns = {'p': 'http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2'}
                
                # Estrazione dei dati principali della fattura
                invoice_data = self.extract_invoice_data(root, ns)

                # Ottieni o crea le aziende
                issuer = self.get_or_create_company(invoice_data['issuer'])
                receiver = self.get_or_create_company(invoice_data['receiver'])

                # Verifica se la fattura esiste già
                existing_invoice = Invoice.objects.filter(
                    invoice_number=invoice_data['invoice_number'],
                    issuer=issuer,
                    invoice_type=invoice_data['invoice_type']
                ).first()

                if existing_invoice:
                    messages.warning(request, f'La fattura n. {invoice_data["invoice_number"]} di {issuer.name} è già presente nel sistema.')
                    return redirect('billing:invoice_upload')

                # Creazione dell'oggetto Invoice
                invoice = Invoice.objects.create(
                    file_xml=xml_file,
                    invoice_number=invoice_data['invoice_number'],
                    invoice_type=invoice_data['invoice_type'],
                    issue_date=invoice_data['issue_date'],
                    currency=invoice_data['currency'],
                    issuer=issuer,
                    receiver=receiver,
                    taxable_amount=invoice_data['taxable_amount'],
                    vat_amount=invoice_data['vat_amount'],
                    total_amount=invoice_data['total_amount'],
                    notes=invoice_data.get('notes', '')
                )

                # Creazione delle righe della fattura
                for line_data in invoice_data['lines']:
                    # Ottieni o crea il prodotto basato sui dati del fornitore
                    product = self.get_or_create_product(
                        line_data['product'], 
                        invoice.issuer
                    )
                    
                    # Gestione dello sconto se presente
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

                messages.success(request, f'Fattura n. {invoice.invoice_number} caricata con successo!')
                return redirect('billing:invoice_upload')

            except Exception as e:
                return render(request, self.template_name, {'form': form, 'error': f'Errore nel parsing del file XML: {e}'})

        else:
            return render(request, self.template_name, {'form': form, 'error': 'Errore nel caricamento del file.'})

    # Il resto del codice rimane invariato
    def extract_invoice_data(self, root, ns):
        """
        Estrae i dati dalla fattura elettronica nel formato XML specificato.
        
        Args:
            root: L'elemento root del file XML
            ns: Dictionary con i namespace XML
            
        Returns:
            Dictionary con i dati estratti dalla fattura
        """
        # Estrazione dei dati principali della fattura dal corpo XML
        header = root.find('.//FatturaElettronicaHeader', ns)
        body = root.find('.//FatturaElettronicaBody', ns)
        
        # Dati generali
        dati_generali = body.find('.//DatiGeneraliDocumento', ns)
        invoice_number = dati_generali.findtext('Numero', namespaces=ns)
        tipo_documento = dati_generali.findtext('TipoDocumento', namespaces=ns)
        
  
        # Conversione data da stringa a oggetto datetime
        issue_date_str = dati_generali.findtext('Data', namespaces=ns)
        issue_date = datetime.datetime.strptime(issue_date_str, '%Y-%m-%d').date() if issue_date_str else None
        
        currency = dati_generali.findtext('Divisa', namespaces=ns)
        total_amount = Decimal(dati_generali.findtext('ImportoTotaleDocumento', namespaces=ns) or '0')

        # Estrazione dei dati del cedente/prestatore (fornitore)
        cedente = header.find('.//CedentePrestatore', ns)
        dati_anagrafici_cedente = cedente.find('.//DatiAnagrafici', ns)
        sede_cedente = cedente.find('.//Sede', ns)
        
        issuer_data = {
            'name': dati_anagrafici_cedente.findtext('.//Denominazione', namespaces=ns),
            'vat_number': dati_anagrafici_cedente.findtext('.//IdFiscaleIVA/IdCodice', namespaces=ns),
            'address': f"{sede_cedente.findtext('Indirizzo', namespaces=ns)} {sede_cedente.findtext('NumeroCivico', namespaces=ns) or ''}",
            'city': sede_cedente.findtext('Comune', namespaces=ns),
            'postal_code': sede_cedente.findtext('CAP', namespaces=ns),
            'country': sede_cedente.findtext('Nazione', namespaces=ns),
            'phone': cedente.findtext('.//Contatti/Telefono', namespaces=ns) or '',
            'email': cedente.findtext('.//Contatti/Email', namespaces=ns) or ''
        }

        # Controlla se il cedente è la nostra azienda
        own_company = CRMCompany.objects.filter(is_own_company=True).first()
        if issuer_data['vat_number']==own_company.vat_number:
            invoice_type = 'OUT'  # Se il cedente è la nostra azienda, è una fattura in uscita
        else:
            invoice_type = 'IN'   # Altrimenti è una fattura in entrata
          

        # Estrazione dei dati del cessionario/committente (cliente)
        cessionario = header.find('.//CessionarioCommittente', ns)
        dati_anagrafici_cessionario = cessionario.find('.//DatiAnagrafici', ns)
        sede_cessionario = cessionario.find('.//Sede', ns)
        
        receiver_data = {
            'name': dati_anagrafici_cessionario.findtext('.//Denominazione', namespaces=ns),
            'vat_number': dati_anagrafici_cessionario.findtext('.//IdFiscaleIVA/IdCodice', namespaces=ns),
            'address': f"{sede_cessionario.findtext('Indirizzo', namespaces=ns)} {sede_cessionario.findtext('NumeroCivico', namespaces=ns) or ''}",
            'city': sede_cessionario.findtext('Comune', namespaces=ns),
            'postal_code': sede_cessionario.findtext('CAP', namespaces=ns),
            'country': sede_cessionario.findtext('Nazione', namespaces=ns),
            'phone': '',  # Non presente nel XML di esempio
            'email': ''   # Non presente nel XML di esempio
        }

        # Estrazione delle righe della fattura
        lines = []
        dettaglio_linee = body.findall('.//DettaglioLinee', ns)
        
        for line in dettaglio_linee:
            description = line.findtext('Descrizione', namespaces=ns) or ''
            
            # Tentativo di estrazione del codice prodotto dal testo della descrizione
            # In questo caso, sembra che BTGSANGIMIGNANO sia un codice prodotto
            external_product_code = ''
            if description and ' ' in description:
                potential_code = description.split(' ')[0]
                if potential_code.isupper():  # Supponiamo che i codici siano in maiuscolo
                    external_product_code = potential_code
            
            # Estrazione dei valori numerici
            try:
                quantity = Decimal(line.findtext('Quantita', namespaces=ns) or '0')
                unit_price = Decimal(line.findtext('PrezzoUnitario', namespaces=ns) or '0')
                line_total = Decimal(line.findtext('PrezzoTotale', namespaces=ns) or '0')
                vat_rate = Decimal(line.findtext('AliquotaIVA', namespaces=ns) or '0')
            except (ValueError, TypeError):
                quantity = Decimal('0')
                unit_price = Decimal('0')
                line_total = Decimal('0')
                vat_rate = Decimal('0')
            
            # Gestione degli sconti
            discount_data = None
            sconto_maggiorazione = line.find('.//ScontoMaggiorazione', ns)
            if sconto_maggiorazione is not None:
                tipo = sconto_maggiorazione.findtext('Tipo', namespaces=ns)
                if tipo == 'SC':  # Sconto
                    percentuale = sconto_maggiorazione.findtext('Percentuale', namespaces=ns)
                    if percentuale:
                        discount_data = {
                            'percentage': Decimal(percentuale),
                            'description': 'Sconto da fattura elettronica'
                        }
            
            line_data = {
                'line_number': int(line.findtext('NumeroLinea', namespaces=ns) or '0'),
                'product': {
                    'name': description,
                    'external_code': external_product_code,
                    'description': description
                },
                'external_product_code': external_product_code,
                'description': description,
                'quantity': quantity,
                'unit_of_measure': line.findtext('UnitaMisura', namespaces=ns) or '',
                'unit_price': unit_price,
                'vat_rate': vat_rate,
                'line_total': line_total,
                'discount': discount_data
            }
            lines.append(line_data)

        # Calcolo degli importi dai dati di riepilogo
        dati_riepilogo = body.findall('.//DatiRiepilogo', ns)
        taxable_amount = Decimal('0')
        vat_amount = Decimal('0')
        
        for riepilogo in dati_riepilogo:
            taxable_amount += Decimal(riepilogo.findtext('ImponibileImporto', namespaces=ns) or '0')
            vat_amount += Decimal(riepilogo.findtext('Imposta', namespaces=ns) or '0')
        
        # Se non abbiamo trovato dati di riepilogo, calcola dalla somma delle righe
        if taxable_amount == 0:
            taxable_amount = sum(line['line_total'] for line in lines)
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
            'notes': ''  # Campo vuoto di default
        }

    def get_or_create_company(self, company_data):
        """
        Ottiene o crea un'azienda basata sui dati estratti dalla fattura.
        """
        # Cerca l'azienda per partita IVA
        company = CRMCompany.objects.filter(vat_number=company_data['vat_number']).first()
        
        if not company:
            # Se non esiste, creala
            company = CRMCompany.objects.create(
                name=company_data['name'],
                vat_number=company_data['vat_number'],
                address=company_data['address'],
                city=company_data['city'],
                postal_code=company_data.get('postal_code', ''),
                country=company_data.get('country', ''),
                phone=company_data.get('phone', ''),
                email=company_data.get('email', ''),
            )
        
        return company

    def get_or_create_product(self, product_data, supplier):
        """
        Ottiene o crea un prodotto basato sui dati della fattura e del fornitore.
        
        Args:
            product_data: Dictionary con i dati del prodotto
            supplier: Oggetto Company rappresentante il fornitore
            
        Returns:
            Oggetto Product
        """
        name = product_data['name']
        description = product_data.get('description', '')
        external_code = product_data.get('external_code', '')
        
        # Prima cerchiamo tramite ProductAlias per questo fornitore
        alias = ProductAlias.objects.filter(
            supplier=supplier,
            alias_name=name
        ).first()
        
        if alias:
            return alias.product
        
        # Se non c'è un alias, cerchiamo il prodotto per nome
        product = Product.objects.filter(name=name).first()
        
        if not product:
            # Se non esiste, creiamo un nuovo prodotto
            product = Product.objects.create(
                name=name,
                description=description
            )
        
        # Creiamo un alias per questo prodotto associato al fornitore
        if external_code or description:
            ProductAlias.objects.create(
                product=product,
                supplier=supplier,
                alias_name=name,
                external_code=external_code,
                description=description
            )
        
        return product

    def get_or_create_discount(self, discount_data):
        """
        Ottiene o crea uno sconto basato sui dati della fattura.
        
        Args:
            discount_data: Dictionary con i dati dello sconto o None
            
        Returns:
            Oggetto Discount o None
        """
        if not discount_data:
            return None
            
        discount, created = Discount.objects.get_or_create(
            percentage=discount_data['percentage'],
            defaults={'description': discount_data.get('description', 'Sconto')}
        )
        
        return discount