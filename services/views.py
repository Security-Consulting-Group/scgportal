from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Service
from .forms import ServiceForm
from django.utils.safestring import mark_safe

class ServiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    permission_required = 'services.view_service'

class ServiceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'
    permission_required = 'services.view_service'

class ServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'
    success_url = reverse_lazy('services:service-list')
    permission_required = 'services.add_service'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request,
                         mark_safe(f"Service '<strong>{self.object.service_name}</strong>' has been created successfully."))
        return response

class ServiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'
    success_url = reverse_lazy('services:service-list')
    permission_required = 'services.change_service'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request,
                      mark_safe(f"Service '<strong>{self.object.service_name}</strong>' has been updated successfully."),
                      extra_tags='alert-primary')
        return response

class ServiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Service
    template_name = 'services/service_confirm_delete.html'
    permission_required = 'services.delete_service'

    def get_success_url(self):
        return reverse_lazy('services:service-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        service_name = self.object.service_name
        self.object.delete()
        messages.warning(self.request,
                         mark_safe(f"Service '<strong>{service_name}</strong>' has been deleted successfully."),
                         extra_tags='alert-warning')
        return HttpResponseRedirect(success_url)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)