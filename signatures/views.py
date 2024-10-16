from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy, reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db.models import Q
from signatures.models import Signature
from signatures.forms import SignatureForm, SignatureUploadForm
from datetime import datetime
import json

class SignatureListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'signatures.view_signature'
    model = Signature
    template_name = 'signatures/signature_list.html'
    context_object_name = 'signatures'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        severity = self.request.GET.get('severity')
        signature_id = self.request.GET.get('id')
        search_query = self.request.GET.get('search')

        if severity:
            queryset = queryset.filter(risk_factor=severity)
        if signature_id:
            queryset = queryset.filter(id=signature_id)
        if search_query:
            queryset = queryset.filter(
                Q(plugin_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['severity_choices'] = Signature.RISK_FACTOR_CHOICES
        return context

class SignatureDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'signatures.view_signature'
    model = Signature
    template_name = 'signatures/signature_detail.html'

class SignatureCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'signatures.add_signature'
    model = Signature
    form_class = SignatureForm
    template_name = 'signatures/signature_form.html'
    success_url = reverse_lazy('signatures:signature_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request,
                         mark_safe(f"Signature <strong>{self.object.plugin_name}</strong> has been created successfully."))
        return response

class SignatureUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'signatures.change_signature'
    model = Signature
    form_class = SignatureForm
    template_name = 'signatures/signature_form.html'
    success_url = reverse_lazy('signatures:signature_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request,
                      mark_safe(f"Signature <strong>{self.object.plugin_name}</strong> has been updated successfully."),
                      extra_tags='alert-primary')
        return response

class SignatureDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'signatures.delete_signature'
    model = Signature
    template_name = 'signatures/signature_confirm_delete.html'
    success_url = reverse_lazy('signatures:signature_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        signature_name = self.object.plugin_name
        self.object.delete()
        messages.warning(self.request,
                       mark_safe(f"Signature <strong>{signature_name}</strong> has been deleted successfully."),
                       extra_tags='alert-warning')
        return HttpResponseRedirect(success_url)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
    
import logging

logger = logging.getLogger(__name__)

class SignatureUploadView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = 'signatures.add_signature'
    template_name = 'signatures/signature_upload.html'
    form_class = SignatureUploadForm
    success_url = reverse_lazy('signatures:signature_list')

    def convert_date(self, date_string):
        try:
            return datetime.strptime(date_string, '%Y/%m/%d').date()
        except ValueError:
            return None

    def form_valid(self, form):
        json_file = form.cleaned_data['json_file']
        scanner_type = form.cleaned_data['scanner_type']
        
        try:
            data = json.load(json_file)
            total_entries = len(data)
            logger.info(f"Total entries in JSON file: {total_entries}")
            new_count = 0
            updated_count = 0
            skipped_count = 0
            error_count = 0
            
            batch_update_time = timezone.now()
            
            for entry in data:
                try:
                    signature, created = Signature.objects.get_or_create(id=entry['id'])
                    
                    if created:
                        new_count += 1
                        logger.info(f"Created new signature with ID: {entry['id']}")
                    else:
                        updated_count += 1
                        logger.info(f"Updated signature with ID: {entry['id']}")
                    
                    # Update all fields
                    for field, value in entry.items():
                        if field in ['cve', 'xref']:
                            setattr(signature, field, json.dumps(value))
                        elif field == 'plugin_modification_date':
                            setattr(signature, field, self.convert_date(value))
                        elif hasattr(signature, field):
                            setattr(signature, field, value)
                    
                    signature.scanner_type = scanner_type
                    signature.scg_last_update = batch_update_time
                    signature.save()
                    
                    logger.info(f"Saved signature {signature.id} with plugin_name: {signature.plugin_name}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing signature with ID: {entry.get('id', 'Unknown')}: {str(e)}")
            
            messages.success(self.request, f'Processed signatures. New: {new_count}, Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}')
            logger.info(f'Processed signatures. New: {new_count}, Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}')
        except Exception as e:
            messages.error(self.request, f'Error processing signatures: {str(e)}')
            logger.error(f'Error processing signatures: {str(e)}')
        
        return super().form_valid(form)