from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
from ..models import Support
from ..forms.support import SupportForm
from inventories.models import Service
from .base import (
    ReportBaseView, ReportListView, ReportDetailView,
    ReportCreateView, ReportDeleteView
)

class SupportReportListView(ReportListView):
    model = Support
    template_name = 'reports/report_list.html'
    permission_required = 'reports.view_support'
    context_object_name = 'reports'

    def get_queryset(self):
        self.service = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        return Support.objects.filter(
            customer=self.request.selected_customer,
            service=self.service
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        return context

class SupportReportDetailView(ReportDetailView):
    model = Support
    template_name = 'reports/support/support_detail.html'
    permission_required = 'reports.view_support'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            pk=self.kwargs['pk'],
            customer=self.request.selected_customer,
            service__service_id=self.kwargs['service_id']
        )

class SupportReportCreateView(ReportCreateView):
    model = Support
    form_class = SupportForm
    template_name = 'reports/support/support_form.html'
    permission_required = 'reports.add_support'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['customer'] = self.request.selected_customer
        kwargs['service'] = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        return kwargs

    def form_valid(self, form):
        form.instance.customer = self.request.selected_customer
        form.instance.service = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        response = super().form_valid(form)
        # messages.success(self.request, mark_safe(f"Support report <strong>{self.object.name}</strong> has been created successfully."), extra_tags='alert-success')
        return response

class SupportReportDeleteView(ReportDeleteView):
    model = Support
    permission_required = 'reports.delete_support'