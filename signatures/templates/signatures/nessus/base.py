from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect

class SignatureBaseView(LoginRequiredMixin, PermissionRequiredMixin):
    model = None  # To be set by subclasses
    context_object_name = 'signature'

class SignatureListView(SignatureBaseView, ListView):
    context_object_name = 'signatures'
    paginate_by = 50

    def get_template_names(self):
        return [f'signatures/{self.kwargs["scanner_type"]}/signature_list.html']

class SignatureDetailView(SignatureBaseView, DetailView):
    def get_template_names(self):
        return [f'signatures/{self.kwargs["scanner_type"]}/signature_detail.html']

class SignatureCreateView(SignatureBaseView, CreateView):
    def get_template_names(self):
        return [f'signatures/{self.kwargs["scanner_type"]}/signature_form.html']

    def get_success_url(self):
        return reverse_lazy('signatures:signature_list', kwargs={'scanner_type': self.kwargs['scanner_type']})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, mark_safe(f"Signature <strong>{self.object.name}</strong> has been created successfully."), extra_tags='alert-success')
        return response

class SignatureUpdateView(SignatureBaseView, UpdateView):
    def get_template_names(self):
        return [f'signatures/{self.kwargs["scanner_type"]}/signature_form.html']

    def get_success_url(self):
        return reverse_lazy('signatures:signature_list', kwargs={'scanner_type': self.kwargs['scanner_type']})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request, mark_safe(f"Signature <strong>{self.object.name}</strong> has been updated successfully."), extra_tags='alert-primary')
        return response

class SignatureDeleteView(SignatureBaseView, DeleteView):
    def get_template_names(self):
        return [f'signatures/{self.kwargs["scanner_type"]}/signature_confirm_delete.html']

    def get_success_url(self):
        return reverse_lazy('signatures:signature_list', kwargs={'scanner_type': self.kwargs['scanner_type']})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        signature_name = self.object.name
        self.object.delete()
        messages.warning(self.request, mark_safe(f"Signature <strong>{signature_name}</strong> has been deleted successfully."), extra_tags='alert-warning')
        return HttpResponseRedirect(success_url)
    
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)