from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from inventories.models import Service, ReportType
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import SelectedCustomerRequiredMixin
from contracts.models import Contract
from django.db.models import Count, Q

from .nessus import (
    NessusReportListView, NessusReportDetailView, NessusReportUploadView, NessusReportDeleteView
)
from .burpsuite import (
    BurpSuiteReportListView, BurpSuiteReportDetailView, BurpSuiteReportUploadView, BurpSuiteReportDeleteView
)
from .support import (
    SupportReportListView, SupportReportDetailView
)

class ReportViewFactory:
    @classmethod
    def get_view_class(cls, service, view_type):
        report_type = service.report_type.name.lower()

        view_mapping = {
            'nessus': {
                'list': NessusReportListView,
                'detail': NessusReportDetailView,
                'upload': NessusReportUploadView,
                'delete': NessusReportDeleteView,
            },
            'burpsuite': {
                'list': BurpSuiteReportListView,
                'detail': BurpSuiteReportDetailView,
                'upload': BurpSuiteReportUploadView,
                'delete': BurpSuiteReportDeleteView,
            },
            'support': {  # Add this section
                'list': SupportReportListView,
                'detail': SupportReportDetailView,
            }
    }

        try:
            return view_mapping[report_type.lower()][view_type]
        except KeyError:
            raise Http404(f"Unsupported report type or view type: {report_type} - {view_type}")

class ReportSelectionView(SelectedCustomerRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'reports/report_selection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active contracts for the selected customer
        active_contracts = Contract.objects.filter(
            customer=self.request.selected_customer,
            contract_status__in=['TRIAL', 'ACTIVE', 'COMPLETED', 'EXPIRED']
        )

        # Get all services associated with active contracts
        services = Service.objects.filter(
            contractservice__contract__in=active_contracts
        ).distinct()

        # Annotate services with report count for the selected customer
        services = services.annotate(
            report_count=Count('nessusreport', filter=Q(nessusreport__customer=self.request.selected_customer), distinct=True) + 
            Count('burpsuitereport', filter=Q(burpsuitereport__customer=self.request.selected_customer), distinct=True)
        )

        # Group services by report type
        services_by_type = {}
        for service in services:
            report_type = service.report_type
            if report_type not in services_by_type:
                services_by_type[report_type] = []
            services_by_type[report_type].append(service)

        context['services_by_type'] = services_by_type
        return context

report_selection_view = ReportSelectionView.as_view()

def report_list_view(request, customer_id, service_id):
    service = get_object_or_404(Service, service_id=service_id)
    view_class = ReportViewFactory.get_view_class(service, 'list')
    return view_class.as_view()(request, customer_id=customer_id, service_id=service_id)

def report_detail_view(request, customer_id, service_id, pk):
    service = get_object_or_404(Service, service_id=service_id)
    view_class = ReportViewFactory.get_view_class(service, 'detail')
    
    # Pass different kwargs based on whether it's a support report
    if service.report_type.name.lower() == 'support':
        return view_class.as_view()(request, customer_id=customer_id, service_id=service_id, contract_id=pk)
    else:
        return view_class.as_view()(request, customer_id=customer_id, service_id=service_id, pk=pk)

def report_upload_view(request, customer_id, service_id):
    service = get_object_or_404(Service, service_id=service_id)
    view_class = ReportViewFactory.get_view_class(service, 'upload')
    return view_class.as_view()(request, customer_id=customer_id, service_id=service_id)

def report_delete_view(request, customer_id, service_id, pk):
    service = get_object_or_404(Service, service_id=service_id)
    view_class = ReportViewFactory.get_view_class(service, 'delete')
    return view_class.as_view()(request, customer_id=customer_id, service_id=service_id, pk=pk)