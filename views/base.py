from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from billing.models.base import Invoice, Payment
from crm.models.base import Company
from billing.forms import InvoiceForm, PaymentForm
from datetime import datetime, timedelta

class SupplierInvoiceListView(View):
    template_name = 'billing/supplier_invoices.html'

    def get(self, request, *args, **kwargs):
        own_company = Company.objects.get(is_own_company=True)
        invoices = Invoice.objects.filter(receiver=own_company)
        form = InvoiceForm()
        return render(request, self.template_name, {'invoices': invoices, 'form': form})

    def post(self, request, *args, **kwargs):
        if 'delete_object' in request.POST:
            invoice = get_object_or_404(Invoice, id=request.POST.get('delete_object'))
            invoice.delete()
            return redirect('billing:supplier_invoices')

        own_company = Company.objects.get(is_own_company=True)
        form = InvoiceForm(request.POST)
        if form.is_valid():
            new_invoice = form.save(commit=False)
            new_invoice.receiver = own_company
            new_invoice.save()
            return redirect('billing:supplier_invoices')

        invoices = Invoice.objects.filter(receiver=own_company)
        return render(request, self.template_name, {'invoices': invoices, 'form': form})

class SupplierInvoiceDetailView(View):
    template_name = 'billing/supplier_invoice_detail.html'

    def get(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        form = InvoiceForm(instance=invoice)
        return render(request, self.template_name, {'invoice': invoice, 'form': form})

    def post(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)

        if 'update_invoice' in request.POST:
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                form.save()
                return redirect('billing:supplier_invoices')

        elif 'delete_invoice' in request.POST:
            invoice.delete()
            return redirect('billing:supplier_invoices')

        return render(request, self.template_name, {'invoice': invoice, 'form': form})

class CustomerInvoiceListView(View):
    template_name = 'billing/customer_invoices.html'

    def get(self, request, *args, **kwargs):
        own_company = Company.objects.get(is_own_company=True)
        invoices = Invoice.objects.filter(issuer=own_company)
        form = InvoiceForm()
        return render(request, self.template_name, {'invoices': invoices, 'form': form})

    def post(self, request, *args, **kwargs):
        if 'delete_object' in request.POST:
            invoice = get_object_or_404(Invoice, id=request.POST.get('delete_object'))
            invoice.delete()
            return redirect('billing:customer_invoices')

        own_company = Company.objects.get(is_own_company=True)
        form = InvoiceForm(request.POST)
        if form.is_valid():
            new_invoice = form.save(commit=False)
            new_invoice.issuer = own_company
            new_invoice.save()
            return redirect('billing:customer_invoices')

        invoices = Invoice.objects.filter(issuer=own_company)
        return render(request, self.template_name, {'invoices': invoices, 'form': form})

class CustomerInvoiceDetailView(View):
    template_name = 'billing/customer_invoice_detail.html'

    def get(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        form = InvoiceForm(instance=invoice)
        return render(request, self.template_name, {'invoice': invoice, 'form': form})

    def post(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, id=invoice_id)

        if 'update_invoice' in request.POST:
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                form.save()
                return redirect('billing:customer_invoices')

        elif 'delete_invoice' in request.POST:
            invoice.delete()
            return redirect('billing:customer_invoices')

        return render(request, self.template_name, {'invoice': invoice, 'form': form})

class PaymentListView(View):
    template_name = 'billing/payments.html'

    def get(self, request, *args, **kwargs):
        twelve_months_ago = datetime.now() - timedelta(days=365)
        payments = Payment.objects.filter(payment_date__gte=twelve_months_ago)
        form = PaymentForm()
        return render(request, self.template_name, {'payments': payments, 'form': form})

    def post(self, request, *args, **kwargs):
        if 'delete_object' in request.POST:
            payment = get_object_or_404(Payment, id=request.POST.get('delete_object'))
            payment.delete()
            return redirect('billing:payments_list')

        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('billing:payments_list')

        twelve_months_ago = datetime.now() - timedelta(days=365)
        payments = Payment.objects.filter(payment_date__gte=twelve_months_ago)
        return render(request, self.template_name, {'payments': payments, 'form': form})
