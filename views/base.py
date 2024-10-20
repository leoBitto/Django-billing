from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from business_finance.models.base import Invoice, InvoiceLineItem, Payment  
from business_finance.forms import *
import os
from datetime import datetime, timedelta



class InvoiceSupplierListView(View):
    template_name = 'business_finance/supplier_invoices.html'

    def get(self, request, *args, **kwargs):
        own_company = Company.objects.get(is_own_company=True)
        invoices = Invoice.objects.filter(customer__company=own_company)
        form = InvoiceForm()  # Form vuoto per la creazione di una nuova fattura
        return render(request, self.template_name, {'invoices': invoices, 'form': form})

    def post(self, request, *args, **kwargs):
        own_company = Company.objects.get(is_own_company=True)

        # Creazione di una nuova fattura tramite POST
        form = InvoiceForm(request.POST)
        if form.is_valid():
            new_invoice = form.save(commit=False)
            new_invoice.customer.company = own_company  # Associa l'azienda come cliente
            new_invoice.save()
            return redirect('business_finance:supplier_invoices')  # Ritorna alla lista dopo aver creato

        # Se non è valido, mostra di nuovo la lista con il form
        invoices = Invoice.objects.filter(customer__company=own_company)
        return render(request, self.template_name, {'invoices': invoices, 'form': form})


class InvoiceSupplierDetailView(View):
    template_name = 'business_finance/supplier_invoice_detail.html'

    def get(self, request, invoice_id, *args, **kwargs):
        # Trova la fattura per ID
        invoice = get_object_or_404(Invoice, id=invoice_id)
        form = InvoiceForm(instance=invoice)
        return render(request, self.template_name, {'invoice': invoice, 'form': form})

    def post(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)

        # Gestisci modifica fattura
        if 'update_invoice' in request.POST:
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                form.save()
                return redirect('business_finance:supplier_invoices')

        # Gestisci eliminazione fattura
        elif 'delete_invoice' in request.POST:
            invoice.delete()
            return redirect('business_finance:supplier_invoices')

        return render(request, self.template_name, {'invoice': invoice, 'form': form})


class InvoiceCustomerListView(View):
    template_name = 'business_finance/customer_invoices.html'

    def get(self, request, *args, **kwargs):
        own_company = Company.objects.get(is_own_company=True)
        invoices = Invoice.objects.filter(supplier__company=own_company)
        form = InvoiceForm()  # Form vuoto per la creazione di una nuova fattura
        return render(request, self.template_name, {'invoices': invoices, 'form': form})

    def post(self, request, *args, **kwargs):
        own_company = Company.objects.get(is_own_company=True)

        # Creazione di una nuova fattura tramite POST
        form = InvoiceForm(request.POST)
        if form.is_valid():
            new_invoice = form.save(commit=False)
            new_invoice.supplier.company = own_company  # Associa l'azienda come fornitore
            new_invoice.save()
            return redirect('business_finance:customer_invoices')  # Ritorna alla lista dopo aver creato

        # Se non è valido, mostra di nuovo la lista con il form
        invoices = Invoice.objects.filter(supplier__company=own_company)
        return render(request, self.template_name, {'invoices': invoices, 'form': form})


class InvoiceCustomerDetailView(View):
    template_name = 'business_finance/customer_invoice_detail.html'

    def get(self, request, invoice_id, *args, **kwargs):
        # Trova la fattura per ID
        invoice = get_object_or_404(Invoice, id=invoice_id)
        form = InvoiceForm(instance=invoice)
        return render(request, self.template_name, {'invoice': invoice, 'form': form})

    def post(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)

        # Gestisci modifica fattura
        if 'update_invoice' in request.POST:
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                form.save()
                return redirect('business_finance:customer_invoices')

        # Gestisci eliminazione fattura
        elif 'delete_invoice' in request.POST:
            invoice.delete()
            return redirect('business_finance:customer_invoices')

        return render(request, self.template_name, {'invoice': invoice, 'form': form})


class PaymentListView(View):
    template_name = 'business_finance/payments.html'

    def get(self, request, *args, **kwargs):
        # Filtra i pagamenti degli ultimi 12 mesi
        twelve_months_ago = datetime.now() - timedelta(days=365)
        payments = Payment.objects.filter(payment_date__gte=twelve_months_ago)

        form = PaymentForm()  # Form vuoto per la creazione di un nuovo pagamento
        return render(request, self.template_name, {'payments': payments, 'form': form})

    def post(self, request, *args, **kwargs):
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()  # Salva il nuovo pagamento
            return redirect('business_finance:payments_list')  # Ritorna alla lista dei pagamenti

        # In caso di errore nel form, torna alla lista con il form non valido
        twelve_months_ago = datetime.now() - timedelta(days=365)
        payments = Payment.objects.filter(payment_date__gte=twelve_months_ago)
        return render(request, self.template_name, {'payments': payments, 'form': form})


class PaymentDetailView(View):
    template_name = 'business_finance/payment_detail.html'

    def get(self, request, payment_id, *args, **kwargs):
        payment = get_object_or_404(Payment, id=payment_id)
        form = PaymentForm(instance=payment)
        return render(request, self.template_name, {'payment': payment, 'form': form})

    def post(self, request, payment_id, *args, **kwargs):
        payment = get_object_or_404(Payment, id=payment_id)

        # Gestisci modifica pagamento
        if 'update_payment' in request.POST:
            form = PaymentForm(request.POST, instance=payment)
            if form.is_valid():
                form.save()
                return redirect('business_finance:payments_list')

        # Gestisci eliminazione pagamento
        elif 'delete_payment' in request.POST:
            payment.delete()
            return redirect('business_finance:payments_list')

        return render(request, self.template_name, {'payment': payment, 'form': form})


class InvoiceSupplierAutoAddView(View):
    template_name = 'business_finance/supplier_invoice_auto_add.html'

    def get(self, request, *args, **kwargs):
        form = InvoiceUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = InvoiceUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # Salviamo il file nella cartella media
            uploaded_file = request.FILES['file']
            file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)

            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Leggiamo il file salvato e parsiamo i dati dal PDF
            text = extract_pdf_data(file_path)
            invoice_data = parse_invoice_data(text)

            # Troviamo o creiamo il fornitore basato sui dati del PDF
            supplier = get_object_or_404(Company, name=invoice_data['supplier'])

            # Creiamo l'oggetto Invoice con i dati reali estratti dal PDF
            invoice = Invoice.objects.create(
                invoice_number=invoice_data['invoice_number'],
                total_amount=invoice_data['total_amount'],
                issue_date=invoice_data['issue_date'],
                supplier=supplier,
                customer=request.user.company  # L'azienda che usa il software è il cliente
            )

            # Creiamo le linee della fattura usando i prodotti estratti
            for product_data in invoice_data['products']:
                # cerca il prodotto

                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    product=None#product_data['description'],  # Da associare al modello `Product` se necessario
                    description=product_data['description'],
                    quantity=product_data['quantity'],
                    unit_price=product_data['unit_price'],
                    vat_rate=invoice_data['vat_rate'],
                    line_total=product_data['line_total']
                )

            # Reindirizza al dettaglio della fattura appena creata
            return redirect('business_finance:invoice_supplier_detail', invoice_id=invoice.id)

        return render(request, self.template_name, {'form': form})


class InvoiceCustomerAutoAddView(View):
    template_name = 'business_finance/customer_invoice_auto_add.html'

    def get(self, request, *args, **kwargs):
        form = InvoiceUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = InvoiceUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # Salviamo il file nella cartella media
            uploaded_file = request.FILES['file']
            file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)

            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Leggiamo il file salvato e parsiamo i dati dal PDF
            text = extract_pdf_data(file_path)
            invoice_data = parse_invoice_data(text)

            # Troviamo o creiamo il cliente basato sui dati del PDF
            customer = get_object_or_404(Company, name=invoice_data['customer'])

            # Creiamo l'oggetto Invoice con i dati reali estratti dal PDF
            invoice = Invoice.objects.create(
                invoice_number=invoice_data['invoice_number'],
                total_amount=invoice_data['total_amount'],
                issue_date=invoice_data['issue_date'],
                supplier=request.user.company,  # L'azienda che usa il software è il fornitore
                customer=customer
            )

            # Creiamo le linee della fattura usando i prodotti estratti
            for product_data in invoice_data['products']:
                # cerca il prodotto 


                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    product=None#product_data['description'],  # Da associare al modello `Product` se necessario
                    description=product_data['description'],
                    quantity=product_data['quantity'],
                    unit_price=product_data['unit_price'],
                    vat_rate=invoice_data['vat_rate'],
                    line_total=product_data['line_total']
                )

            # Reindirizza al dettaglio della fattura appena creata
            return redirect('business_finance:invoice_customer_detail', invoice_id=invoice.id)

        return render(request, self.template_name, {'form': form})