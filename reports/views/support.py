from django.shortcuts import get_object_or_404
from .base import ReportListView, ReportDetailView
from ..models import SupportReport
from inventories.models import Service
from engagements.models import Engagement, TimeEntry
from customers.models import Customer
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from contracts.models import Contract
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce


class SupportReportListView(ReportListView):
    model = SupportReport
    template_name = 'reports/report_list.html'
    permission_required = 'reports.view_supportreport'
    
    def get_queryset(self):
        self.service = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        self.customer = get_object_or_404(Customer, customer_id=self.kwargs['customer_id'])
        
        return Contract.objects.filter(
            customer=self.customer,
            contractservice__service=self.service
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        context['customer'] = self.customer
        context['is_support_report'] = True
        
        for contract in context['reports']:
            engagement = Engagement.objects.filter(
                contract=contract,
                contract_service__service=self.service
            ).first()
            if engagement:
                contract.total_hours = engagement.total_service_hours
                contract.remaining_hours = engagement.remaining_service_hours
                contract.contracted_hours = engagement.contract_service.quantity
                contract.engagement_count = Engagement.objects.filter(
                    contract=contract,
                    contract_service__service=self.service
                ).count()
        
        return context

class SupportReportDetailView(ReportDetailView):
    model = Contract  # Add this
    template_name = 'reports/support/report_detail.html'
    permission_required = 'reports.view_supportreport'
    
    def get_object(self, queryset=None):
        return get_object_or_404(
            Contract,
            contract_id=self.kwargs['contract_id'],
            customer__customer_id=self.kwargs['customer_id']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract'] = self.object
        context['service'] = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        
        # Get sort parameters
        sort_by = self.request.GET.get('sort', '-created_at')
        
        # Build the base queryset
        engagements = Engagement.objects.filter(
            contract=self.object,
            contract_service__service__service_id=self.kwargs['service_id']
        ).select_related(
            'contract_service'
        ).prefetch_related(
            'timeentry_set'
        ).annotate(
            total_hours=Coalesce(Sum('timeentry__hours_spent'), 0, output_field=DecimalField())
        )

        # Handle hours sorting separately
        if sort_by == 'hours_used':
            engagements = engagements.order_by('total_hours')
        elif sort_by == '-hours_used':
            engagements = engagements.order_by('-total_hours')
        else:
            engagements = engagements.order_by(sort_by)
        
        # Get time entry data by date for the histogram
        time_entries_by_date = TimeEntry.objects.filter(
            engagement__contract=self.object,
            engagement__contract_service__service__service_id=self.kwargs['service_id']
        ).annotate(
            date_only=TruncDate('date')
        ).values('date_only').annotate(
            total_hours=Sum('hours_spent')
        ).order_by('date_only')

        # Format the dates for JSON
        formatted_entries = [
            {
                'date_only': entry['date_only'].strftime('%Y-%m-%d'),
                'total_hours': float(entry['total_hours'])
            }
            for entry in time_entries_by_date
        ]

        context.update({
            'engagements': engagements,
            'time_entries_by_date': formatted_entries,
            'sort_by': sort_by,
            'customer': self.object.customer,
        })
        
        return context