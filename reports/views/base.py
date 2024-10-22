from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.mixins import SelectedCustomerRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect

class ReportBaseView(SelectedCustomerRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin):
    model = None  # To be set by subclasses
    context_object_name = 'report'

class ReportListView(ReportBaseView, ListView):
    context_object_name = 'reports'
    paginate_by = 10
    template_name = 'reports/report_list.html'

class ReportDetailView(ReportBaseView, DetailView):
    template_name = 'reports/report_detail.html'

class ReportCreateView(ReportBaseView, CreateView):
    template_name = 'reports/report_form.html'

    def get_success_url(self):
        return reverse_lazy('reports:report_list', kwargs={
            'customer_id': self.request.selected_customer.customer_id,
            'service_id': self.object.service.service_id  # Changed from report_type to service_id
        })

    def form_valid(self, form):
        form.instance.customer = self.request.selected_customer
        response = super().form_valid(form)
        messages.success(self.request, mark_safe(f"Report <strong>{self.object.name}</strong> has been created successfully."), extra_tags='alert-success')
        return response

class ReportUpdateView(ReportBaseView, UpdateView):
    template_name = 'reports/report_form.html'

    def get_success_url(self):
        return reverse_lazy('reports:report_list', kwargs={
            'customer_id': self.request.selected_customer.customer_id,
            'report_type': self.kwargs['report_type']
        })

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request, mark_safe(f"Report <strong>{self.object.name}</strong> has been updated successfully."), extra_tags='alert-primary')
        return response

class ReportDeleteView(ReportBaseView, DeleteView):
    def get_template_names(self):
        return [f'reports/report_confirm_delete.html']
        # return [f'reports/{self.kwargs["report_type"]}/report_confirm_delete.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.object.service
        return context

    def get_success_url(self):
        return reverse_lazy('reports:report_list', kwargs={
            'customer_id': self.request.selected_customer.customer_id,
            'service_id': self.object.service.service_id
        })

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        report_name = self.object.name
        self.object.delete()
        messages.warning(self.request, mark_safe(f"Report <strong>{report_name}</strong> has been deleted successfully."), extra_tags='alert-warning')
        return HttpResponseRedirect(success_url)
    
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)