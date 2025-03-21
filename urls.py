from django.urls import path
from billing.views.base import *
from billing.views.parser import *

app_name = 'billing'

urlpatterns = [
    # Supplier Invoice URLs
    path('supplier-invoices/', SupplierInvoiceListView.as_view(), name='supplier_invoices'),
    path('supplier-invoices/<int:invoice_id>/', SupplierInvoiceDetailView.as_view(), name='supplier_invoice_detail'),
    
    # Customer Invoice URLs
    path('customer-invoices/', CustomerInvoiceListView.as_view(), name='customer_invoices'),
    path('customer-invoices/<int:invoice_id>/', CustomerInvoiceDetailView.as_view(), name='customer_invoice_detail'),
    
    # Invoice Upload URLs
    path('invoice-upload/', InvoiceUploadView.as_view(), name='invoice_upload'),
    path('invoice-upload-ajax/', InvoiceUploadAjaxView.as_view(), name='invoice_upload_ajax'),
]