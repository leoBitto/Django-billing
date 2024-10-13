from django.urls import path
from .views import (  # Assicurati di importare correttamente le views
    InvoiceSupplierListView,
    InvoiceSupplierDetailView,
    InvoiceCustomerListView,
    InvoiceCustomerDetailView,
    PaymentListView,
    PaymentDetailView,
    InvoiceSupplierAutoAddView,
    InvoiceCustomerAutoAddView,
)

app_name = 'business_finance'

urlpatterns = [
    path('invoice-supplier/', InvoiceSupplierListView.as_view(), name='invoice_supplier_list'),
    path('invoice-ensuppliertry/<int:invoice_id>/', InvoiceSupplierDetailView.as_view(), name='invoice_supplier_detail'),
    path('invoice-esupplierntry-auto-add/', InvoiceSupplierAutoAddView.as_view(), name='invoice_supplier_auto_add'),

    path('invoice-customer/', InvoiceCustomerListView.as_view(), name='invoice_customer_list'),
    path('invoice-customer/<int:invoice_id>/', InvoiceCustomerDetailView.as_view(), name='invoice_customer_detail'),
    path('invoice-customer-auto-add/', InvoiceCustomerAutoAddView.as_view(), name='invoice_customer_auto_add'),

    path('payment/', PaymentListView.as_view(), name='payments_list'),
    path('payment/<int:payment_id>/', PaymentDetailView.as_view(), name='payment_detail'),
]
