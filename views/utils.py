import re
import pymupdf  

def parse_invoice_data(text):
    """
    Cerca i campi chiave nel testo del PDF e restituisce un dizionario con i dati della fattura.
    """
    invoice_data = {}

    # Estrai il numero della fattura
    invoice_number_match = re.search(r'Fattura n\.\s*(\d+)', text)
    invoice_data['invoice_number'] = invoice_number_match.group(1) if invoice_number_match else None

    # Estrai la data della fattura (Data Documento)
    issue_date_match = re.search(r'Data Documento:\s*([\d/]+)', text)
    invoice_data['issue_date'] = issue_date_match.group(1) if issue_date_match else None

    # Estrai il totale del documento
    total_amount_match = re.search(r'Totale Documento:\s*([\d,.]+)', text)
    invoice_data['total_amount'] = total_amount_match.group(1).replace(',', '.') if total_amount_match else None

    # Estrai i dati del fornitore
    supplier_match = re.search(r'Cedente/Prestatore:\s*(.*)', text)
    invoice_data['supplier'] = supplier_match.group(1) if supplier_match else None

    # Estrai i dati del cliente
    customer_match = re.search(r'Cessionario/Committente:\s*(.*)', text)
    invoice_data['customer'] = customer_match.group(1) if customer_match else None

    # Estrai i prodotti e le linee della fattura (Descrizione, quantità, prezzo unitario, sconto, totale)
    products = []
    product_lines = re.findall(
        r'Descrizione\s*(.*?)\s*Quantità\s*(\d+)\s*Prezzo Unitario:\s*([\d,.]+)\s*Sconto:\s*([\d,.]+)%\s*Totale Linea:\s*([\d,.]+)',
        text
    )

    for line in product_lines:
        product = {
            'description': line[0],
            'quantity': int(line[1]),
            'unit_price': line[2].replace(',', '.'),
            'discount': line[3].replace(',', '.'),
            'line_total': line[4].replace(',', '.')
        }
        products.append(product)

    invoice_data['products'] = products

    # Estrai l'aliquota IVA
    vat_rate_match = re.search(r'Aliquota IVA:\s*([\d,.]+)%', text)
    invoice_data['vat_rate'] = vat_rate_match.group(1).replace(',', '.') if vat_rate_match else None

    return invoice_data



def extract_pdf_data(pdf_file):
    """
    Estrae le informazioni principali dal PDF passato e restituisce un dizionario.
    """
    doc = pymupdf.open(pdf_file)
    text = ""

    # Unisci il testo di tutte le pagine in una stringa
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text("text")

    return text  # Restituiamo il testo grezzo da analizzare