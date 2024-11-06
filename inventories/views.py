from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from .models import Service, ReportType
from .forms import ServiceForm, ReportTypeForm

class InventorySelectionView(LoginRequiredMixin, TemplateView):
    template_name = 'inventories/inventory_selection.html'

# Service Views
class ServiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Service
    template_name = 'inventories/services/service_list.html'
    context_object_name = 'services'
    permission_required = 'inventories.view_service'

class ServiceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Service
    template_name = 'inventories/services/service_detail.html'
    context_object_name = 'service'
    permission_required = 'inventories.view_service'

class ServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'inventories/services/service_form.html'
    success_url = reverse_lazy('inventories:service_list')
    permission_required = 'inventories.add_service'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request,
                         mark_safe(f"Service '<strong>{self.object.service_name}</strong>' has been created successfully."))
        return response

class ServiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'inventories/services/service_form.html'
    success_url = reverse_lazy('inventories:service_list')
    permission_required = 'inventories.change_service'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request,
                      mark_safe(f"Service '<strong>{self.object.service_name}</strong>' has been updated successfully."),
                      extra_tags='alert-primary')
        return response

class ServiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Service
    template_name = 'inventories/services/service_confirm_delete.html'
    permission_required = 'inventories.delete_service'

    def get_success_url(self):
        return reverse_lazy('inventories:service_list')

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

# ReportType Views
class ReportTypeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ReportType
    template_name = 'inventories/report_types/reporttype_list.html'
    context_object_name = 'reporttypes'
    permission_required = 'inventories.view_reporttype'

class ReportTypeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ReportType
    template_name = 'inventories/report_types/reporttype_detail.html'
    context_object_name = 'reporttype'
    permission_required = 'inventories.view_reporttype'

class ReportTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ReportType
    form_class = ReportTypeForm
    template_name = 'inventories/report_types/reporttype_form.html'
    success_url = reverse_lazy('inventories:reporttype_list')
    permission_required = 'inventories.add_reporttype'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request,
                         mark_safe(f"Report Type '<strong>{self.object.name}</strong>' has been created successfully."))
        return response

class ReportTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ReportType
    form_class = ReportTypeForm
    template_name = 'inventories/report_types/reporttype_form.html'
    success_url = reverse_lazy('inventories:reporttype_list')
    permission_required = 'inventories.change_reporttype'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request,
                      mark_safe(f"Report Type '<strong>{self.object.name}</strong>' has been updated successfully."),
                      extra_tags='alert-primary')
        return response

class ReportTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ReportType
    template_name = 'inventories/report_types/reporttype_confirm_delete.html'
    permission_required = 'inventories.delete_reporttype'

    def get_success_url(self):
        return reverse_lazy('inventories:reporttype_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        reporttype_name = self.object.name
        self.object.delete()
        messages.warning(self.request,
                         mark_safe(f"Report Type '<strong>{reporttype_name}</strong>' has been deleted successfully."),
                         extra_tags='alert-warning')
        return HttpResponseRedirect(success_url)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)