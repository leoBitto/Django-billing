# billing/views/invoice_views.py
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from billing.forms import InvoiceUploadForm
from billing.services.invoice_parser import InvoiceParser

class InvoiceUploadView(View):
    template_name = 'billing/invoice_upload.html'

    def get(self, request):
        form = InvoiceUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = InvoiceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            return render(request, self.template_name, {'form': form})
        else:
            return render(request, self.template_name, {'form': form, 'error': 'Errore nel caricamento dei file.'})

@method_decorator(csrf_exempt, name='dispatch')
class InvoiceUploadAjaxView(View):
    """
    View per gestire il caricamento asincrono delle fatture
    """
    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({'status': 'error', 'message': 'Nessun file ricevuto'}, status=400)
        
        xml_file = request.FILES['file']
        
        # Verifica se è un file XML (controllo di base)
        if not xml_file.name.lower().endswith('.xml'):
            return JsonResponse({
                'status': 'error', 
                'message': 'Il file deve essere in formato XML'
            }, status=400)
        
        # Elabora il file
        parser = InvoiceParser()
        invoice, status, message = parser.parse_and_save(xml_file)
        
        return JsonResponse({
            'filename': xml_file.name,
            'status': status,
            'message': message
        })