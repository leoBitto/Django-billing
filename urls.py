from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Supplier Invoice URLs
    path('supplier-invoices/', views.SupplierInvoiceListView.as_view(), name='supplier_invoices'),
    path('supplier-invoices/<int:invoice_id>/', views.SupplierInvoiceDetailView.as_view(), name='supplier_invoice_detail'),
    
    # Customer Invoice URLs
    path('customer-invoices/', views.CustomerInvoiceListView.as_view(), name='customer_invoices'),
    path('customer-invoices/<int:invoice_id>/', views.CustomerInvoiceDetailView.as_view(), name='customer_invoice_detail'),
    
]