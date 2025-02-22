from django.contrib import admin
from .models.base import Discount, Invoice, InvoiceLine

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('percentage', 'description')
    search_fields = ('description',)

class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1
    autocomplete_fields = ['product', 'discount']

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'invoice_type', 'issue_date', 'issuer', 'receiver', 'total_amount')
    list_filter = ('invoice_type', 'issue_date')
    search_fields = ('invoice_number', 'issuer__name', 'receiver__name')
    inlines = [InvoiceLineInline]
    autocomplete_fields = ['issuer', 'receiver']

class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'line_number', 'product', 'quantity', 'unit_price', 'line_total')
    search_fields = ('invoice__invoice_number', 'product__name')
    autocomplete_fields = ['invoice', 'product', 'discount']

admin.site.register(Discount, DiscountAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceLine, InvoiceLineAdmin)
