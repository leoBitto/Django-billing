# billing/services/invoice_parser.py
from decimal import Decimal
import datetime
from xml.etree import ElementTree as ET
from billing.models.base import Invoice, InvoiceLine, Discount
from warehouse.models.base import Product, ProductAlias
from crm.models.base import Company as CRMCompany

class InvoiceParser:
    """
    Classe responsabile del parsing e della persistenza delle fatture XML
    """
    
    def __init__(self):
        self.ns = {'p': 'http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2'}
    
    def parse_and_save(self, xml_file):
        """
        Parsa un file XML di fattura e salva i dati nel database
        
        Args:
            xml_file: File XML da parsare
            
        Returns:
            tuple: (invoice, status, message) dove status può essere 'success', 'duplicate', 'error'
        """
        try:
            # Parsing del file XML
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Estrazione dei dati principali della fattura
            invoice_data = self.extract_invoice_data(root)

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
                return None, 'duplicate', f'La fattura n. {invoice_data["invoice_number"]} di {issuer.name} è già presente nel sistema.'

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

            return invoice, 'success', f'Fattura n. {invoice.invoice_number} di {issuer.name} caricata con successo!'
            
        except Exception as e:
            return None, 'error', f'Errore nel parsing del file {xml_file.name}: {str(e)}'

    def extract_invoice_data(self, root):
        """
        Estrae i dati dalla fattura elettronica nel formato XML specificato.
        """
        # Estrazione dei dati principali della fattura dal corpo XML
        header = root.find('.//FatturaElettronicaHeader', self.ns)
        body = root.find('.//FatturaElettronicaBody', self.ns)
        
        # Dati generali
        dati_generali = body.find('.//DatiGeneraliDocumento', self.ns)
        invoice_number = dati_generali.findtext('Numero', namespaces=self.ns)
        tipo_documento = dati_generali.findtext('TipoDocumento', namespaces=self.ns)
        
        # Conversione data da stringa a oggetto datetime
        issue_date_str = dati_generali.findtext('Data', namespaces=self.ns)
        issue_date = datetime.datetime.strptime(issue_date_str, '%Y-%m-%d').date() if issue_date_str else None
        
        currency = dati_generali.findtext('Divisa', namespaces=self.ns)
        total_amount = Decimal(dati_generali.findtext('ImportoTotaleDocumento', namespaces=self.ns) or '0')

        # Estrazione dei dati del cedente/prestatore (fornitore)
        cedente = header.find('.//CedentePrestatore', self.ns)
        dati_anagrafici_cedente = cedente.find('.//DatiAnagrafici', self.ns)
        sede_cedente = cedente.find('.//Sede', self.ns)
        
        issuer_data = {
            'name': dati_anagrafici_cedente.findtext('.//Denominazione', namespaces=self.ns),
            'vat_number': dati_anagrafici_cedente.findtext('.//IdFiscaleIVA/IdCodice', namespaces=self.ns),
            'address': f"{sede_cedente.findtext('Indirizzo', namespaces=self.ns)} {sede_cedente.findtext('NumeroCivico', namespaces=self.ns) or ''}",
            'city': sede_cedente.findtext('Comune', namespaces=self.ns),
            'postal_code': sede_cedente.findtext('CAP', namespaces=self.ns),
            'country': sede_cedente.findtext('Nazione', namespaces=self.ns),
            'phone': cedente.findtext('.//Contatti/Telefono', namespaces=self.ns) or '',
            'email': cedente.findtext('.//Contatti/Email', namespaces=self.ns) or ''
        }

        # Controlla se il cedente è la nostra azienda
        own_company = CRMCompany.objects.filter(is_own_company=True).first()
        if issuer_data['vat_number']==own_company.vat_number:
            invoice_type = 'OUT'  # Se il cedente è la nostra azienda, è una fattura in uscita
        else:
            invoice_type = 'IN'   # Altrimenti è una fattura in entrata
          
        # Estrazione dei dati del cessionario/committente (cliente)
        cessionario = header.find('.//CessionarioCommittente', self.ns)
        dati_anagrafici_cessionario = cessionario.find('.//DatiAnagrafici', self.ns)
        sede_cessionario = cessionario.find('.//Sede', self.ns)
        
        receiver_data = {
            'name': dati_anagrafici_cessionario.findtext('.//Denominazione', namespaces=self.ns),
            'vat_number': dati_anagrafici_cessionario.findtext('.//IdFiscaleIVA/IdCodice', namespaces=self.ns),
            'address': f"{sede_cessionario.findtext('Indirizzo', namespaces=self.ns)} {sede_cessionario.findtext('NumeroCivico', namespaces=self.ns) or ''}",
            'city': sede_cessionario.findtext('Comune', namespaces=self.ns),
            'postal_code': sede_cessionario.findtext('CAP', namespaces=self.ns),
            'country': sede_cessionario.findtext('Nazione', namespaces=self.ns),
            'phone': '',  # Non presente nel XML di esempio
            'email': ''   # Non presente nel XML di esempio
        }

        # Estrazione delle righe della fattura
        lines = []
        dettaglio_linee = body.findall('.//DettaglioLinee', self.ns)
        
        for line in dettaglio_linee:
            description = line.findtext('Descrizione', namespaces=self.ns) or ''
            
            # Tentativo di estrazione del codice prodotto
            external_product_code = ''
            if description and ' ' in description:
                potential_code = description.split(' ')[0]
                if potential_code.isupper():  # Supponiamo che i codici siano in maiuscolo
                    external_product_code = potential_code
            
            # Estrazione dei valori numerici
            try:
                quantity = Decimal(line.findtext('Quantita', namespaces=self.ns) or '0')
                unit_price = Decimal(line.findtext('PrezzoUnitario', namespaces=self.ns) or '0')
                line_total = Decimal(line.findtext('PrezzoTotale', namespaces=self.ns) or '0')
                vat_rate = Decimal(line.findtext('AliquotaIVA', namespaces=self.ns) or '0')
            except (ValueError, TypeError):
                quantity = Decimal('0')
                unit_price = Decimal('0')
                line_total = Decimal('0')
                vat_rate = Decimal('0')
            
            # Gestione degli sconti
            discount_data = None
            sconto_maggiorazione = line.find('.//ScontoMaggiorazione', self.ns)
            if sconto_maggiorazione is not None:
                tipo = sconto_maggiorazione.findtext('Tipo', namespaces=self.ns)
                if tipo == 'SC':  # Sconto
                    percentuale = sconto_maggiorazione.findtext('Percentuale', namespaces=self.ns)
                    if percentuale:
                        discount_data = {
                            'percentage': Decimal(percentuale),
                            'description': 'Sconto da fattura elettronica'
                        }
            
            line_data = {
                'line_number': int(line.findtext('NumeroLinea', namespaces=self.ns) or '0'),
                'product': {
                    'name': description,
                    'external_code': external_product_code,
                    'description': description
                },
                'external_product_code': external_product_code,
                'description': description,
                'quantity': quantity,
                'unit_of_measure': line.findtext('UnitaMisura', namespaces=self.ns) or '',
                'unit_price': unit_price,
                'vat_rate': vat_rate,
                'line_total': line_total,
                'discount': discount_data
            }
            lines.append(line_data)

        # Calcolo degli importi dai dati di riepilogo
        dati_riepilogo = body.findall('.//DatiRiepilogo', self.ns)
        taxable_amount = Decimal('0')
        vat_amount = Decimal('0')
        
        for riepilogo in dati_riepilogo:
            taxable_amount += Decimal(riepilogo.findtext('ImponibileImporto', namespaces=self.ns) or '0')
            vat_amount += Decimal(riepilogo.findtext('Imposta', namespaces=self.ns) or '0')
        
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
        """
        if not discount_data:
            return None
            
        discount, created = Discount.objects.get_or_create(
            percentage=discount_data['percentage'],
            defaults={'description': discount_data.get('description', 'Sconto')}
        )
        
        return discount