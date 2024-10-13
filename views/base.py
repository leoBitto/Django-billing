from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Invoice, Payment  # Assicurati di importare i tuoi modelli
from .forms import InvoiceForm, PaymentForm  # Importa i tuoi form

class InvoiceSupplierListView(View):
    template_name = 'business_finance/supplier_invoices.html'

    def get(self, request, *args, **kwargs):
        invoices = Invoice.objects.filter(supplier=request.user)  # Cambia in base alla tua logica
        return render(request, self.template_name, {'invoices': invoices})

class InvoiceSupplierDetailView(View):
    template_name = 'business_finance/supplier_invoice_detail.html'

    def get(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        return render(request, self.template_name, {'invoice': invoice})

    def post(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            return redirect('business_finance:invoice_supplier')  # Modifica l'URL se necessario
        return render(request, self.template_name, {'invoice': invoice, 'form': form})

class InvoiceCustomerListView(View):
    template_name = 'business_finance/customer_invoices.html'

    def get(self, request, *args, **kwargs):
        invoices = Invoice.objects.filter(customer=request.user)  # Cambia in base alla tua logica
        return render(request, self.template_name, {'invoices': invoices})

class InvoiceCustomerDetailView(View):
    template_name = 'business_finance/customer_invoice_detail.html'

    def get(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        return render(request, self.template_name, {'invoice': invoice})

    def post(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            return redirect('business_finance:invoice_customer')  # Modifica l'URL se necessario
        return render(request, self.template_name, {'invoice': invoice, 'form': form})

class PaymentListView(View):
    template_name = 'business_finance/payments.html'

    def get(self, request, *args, **kwargs):
        payments = Payment.objects.filter(user=request.user)  # Cambia in base alla tua logica
        return render(request, self.template_name, {'payments': payments})

class PaymentDetailView(View):
    template_name = 'business_finance/payment_detail.html'

    def get(self, request, payment_id, *args, **kwargs):
        payment = get_object_or_404(Payment, id=payment_id)
        return render(request, self.template_name, {'payment': payment})

    def post(self, request, payment_id, *args, **kwargs):
        payment = get_object_or_404(Payment, id=payment_id)
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect('business_finance:payments_list')  # Modifica l'URL se necessario
        return render(request, self.template_name, {'payment': payment, 'form': form})

class InvoiceSupplierAutoAddView(View):
    template_name = 'business_finance/supplier_invoice_auto_add.html'

    def get(self, request, *args, **kwargs):
        # Logica per il caricamento automatico
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        # Logica per gestire il caricamento automatico
        pass

class InvoiceCustomerAutoAddView(View):
    template_name = 'business_finance/customer_invoice_auto_add.html'

    def get(self, request, *args, **kwargs):
        # Logica per il caricamento automatico
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        # Logica per gestire il caricamento automatico
        pass
