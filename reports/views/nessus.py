from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db import transaction
from django.http import JsonResponse
from core.mixins import SelectedCustomerRequiredMixin
from .base import ReportListView, ReportDetailView, ReportDeleteView #, ReportUpdateView
from ..models import NessusReport, NessusVulnerability
from ..forms.nessus import NessusReportUploadForm
from signatures.models import NessusSignature
from ..views.mixins import StatusSummaryMixin
from inventories.models import Service
import json
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from .base import ReportBaseView
from collections import defaultdict
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils.decorators import method_decorator
from django.utils import timezone

class NessusReportListView(ReportListView):
    model = NessusReport
    template_name = 'reports/report_list.html'
    permission_required = 'reports.view_nessusreport'
    context_object_name = 'reports'

    def get_queryset(self):
        self.service = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        return NessusReport.objects.filter(
            customer=self.request.selected_customer,
            service=self.service
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        return context

class NessusReportDetailView(StatusSummaryMixin, ReportDetailView):
    model = NessusReport
    template_name = 'reports/nessus/report_detail.html'
    context_object_name = 'report'
    permission_required = 'reports.view_nessusreport'
    
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            pk=self.kwargs['pk'],
            customer=self.request.selected_customer,
            service__service_id=self.kwargs['service_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vulnerabilities = self.object.vulnerabilities.select_related('signature').all()

        status_summary = {}
        for status_value, status_label in NessusVulnerability.STATUS_CHOICES:
            count = vulnerabilities.filter(status=status_value).count()
            if count > 0:  # Only include statuses that have targets
                status_summary[status_label] = count
        
        context['status_summary'] = status_summary
        
        context['STATUS_CHOICES'] = NessusVulnerability.STATUS_CHOICES
        
        # Fetch the latest change information for each vulnerability
        latest_changes = vulnerabilities.values(
            'signature', 'target_affected'
        ).annotate(
            latest_change=models.Max('changed_at'),
            changed_by_id=models.F('changed_by')
        )

        # Fetch user information
        user_ids = set(change['changed_by_id'] for change in latest_changes if change['changed_by_id'] is not None)
        User = get_user_model()
        user_dict = {user.id: user for user in User.objects.filter(id__in=user_ids)}

        # Function to order risk factors by severity
        def severity_order(risk_factor):
            order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Informational': 4, 'None': 5}
            return order.get(risk_factor, 6)
        
        grouped_vulnerabilities = defaultdict(lambda: defaultdict(list))
        for vuln in vulnerabilities:
            # Process references (previously see_also)
            if vuln.signature.references:
                vuln.signature.references = vuln.signature.references.split()
            
            # Process CVEs
            if vuln.signature.cve:
                try:
                    cve_list = json.loads(vuln.signature.cve)
                    vuln.signature.cve = [cve.strip().replace('"', '').replace(' ', '') for cve in cve_list if cve.strip()]
                except json.JSONDecodeError:
                    vuln.signature.cve = []

            # Format the changed_at date for each vulnerability
            if vuln.changed_at:
                formatted_change_date = timezone.localtime(vuln.changed_at).strftime('%b %d, %Y, %I:%M:%S %p')
            else:
                formatted_change_date = 'N/A'
            
            grouped_vulnerabilities[vuln.signature.risk_factor][vuln.signature.id].append({
                'signature': vuln.signature,
                'targets': [{
                    'id': vuln.id,
                    'target_affected': vuln.target_affected,
                    'status': vuln.status,
                    'changed_at': formatted_change_date,
                    'changed_by': vuln.changed_by.email if vuln.changed_by else 'N/A',
                    'STATUS_CHOICES': NessusVulnerability.STATUS_CHOICES  # Add this line
                }]
            })

        # Sort the grouped vulnerabilities
        sorted_vulnerabilities = []
        for risk_factor, signatures in sorted(grouped_vulnerabilities.items(), key=lambda x: severity_order(x[0])):
            vuln_group = {
                'risk_factor': risk_factor,
                'vulnerabilities': []
            }
            for signature_id, vulns in signatures.items():
                vuln_group['vulnerabilities'].append({
                    'signature': vulns[0]['signature'],
                    'targets': [target for vuln in vulns for target in vuln['targets']]
                })
            sorted_vulnerabilities.append(vuln_group)
        
        context['grouped_vulnerabilities'] = sorted_vulnerabilities
        return context

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        return self.update_vulnerability_status(request, *args, **kwargs)

    def update_vulnerability_status(self, request, *args, **kwargs):
        vulnerability_id = request.POST.get('vulnerability_id')
        new_status = request.POST.get('status')
        bulk_type = request.POST.get('bulk_type')
        risk_factor = request.POST.get('risk_factor')

        try:
            with transaction.atomic():
                report = self.get_object()
                updated_vulnerabilities = []

                if bulk_type == 'vulnerability':
                    vulnerabilities = NessusVulnerability.objects.filter(
                        report=report,
                        signature_id=NessusVulnerability.objects.get(id=vulnerability_id).signature_id
                    )
                elif bulk_type == 'risk_factor':
                    vulnerabilities = NessusVulnerability.objects.filter(
                        report=report,
                        signature__risk_factor=risk_factor
                    )
                else:
                    vulnerabilities = NessusVulnerability.objects.filter(id=vulnerability_id, report=report)

                for vulnerability in vulnerabilities:
                    if vulnerability.status != new_status:
                        vulnerability.status = new_status
                        vulnerability.changed_by = request.user  # This is now correct
                        vulnerability.save()

                        updated_vulnerabilities.append({
                            'id': vulnerability.id,
                            'target_affected': vulnerability.target_affected,
                            'status': new_status,
                            'changed_by': request.user.email,
                            'changed_at': timezone.localtime(vulnerability.changed_at).strftime('%b %d, %Y, %I:%M:%S %p')
                        })

                return JsonResponse({
                    'success': True, 
                    'new_status': dict(NessusVulnerability.STATUS_CHOICES)[new_status],
                    'updated_count': len(updated_vulnerabilities),
                    'updated_vulnerabilities': updated_vulnerabilities,
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    def post(self, request, *args, **kwargs):
        return self.update_vulnerability_status(request, *args, **kwargs)


class NessusReportUploadView(ReportBaseView, FormView):
    form_class = NessusReportUploadForm
    template_name = 'reports/report_upload.html'
    permission_required = 'reports.add_nessusreport'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['customer'] = self.request.selected_customer
        kwargs['service'] = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        return kwargs

    def form_valid(self, form):
        json_file = form.cleaned_data['json_file']
        contract = form.cleaned_data.get('contract')
        service = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        report_name = form.cleaned_data.get('name')

        try:
            data = json.load(json_file)

            with transaction.atomic():
                self.object = NessusReport.objects.create(
                    customer=self.request.selected_customer,
                    contract=contract,
                    service=service,
                    date=data['date'],
                    inventory=data['inventory'],
                    name=report_name,
                )

                for alert in data['alert_report']:
                    try:
                        signature = NessusSignature.objects.get(id=alert['plugin_id'])
                        
                        NessusVulnerability.objects.create(
                            report=self.object,
                            signature=signature,
                            target_affected=alert['target_affected'],
                            operating_system=alert['os'],
                            status='not_started'
                        )

                    except NessusSignature.DoesNotExist:
                        messages.warning(self.request,
                                        mark_safe(f"Signature with ID <strong>{alert['plugin_id']}</strong> not found."),
                                        extra_tags='alert-warning')

                messages.success(self.request,
                                mark_safe(f"Nessus Report <strong>{self.object.report_id}</strong> uploaded successfully."))

        except json.JSONDecodeError:
            messages.error(self.request, "Invalid JSON file.", extra_tags='alert-danger')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request,
                           mark_safe(f"Error uploading report: <strong>{str(e)}</strong>"),
                           extra_tags='alert-danger')
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        context['report_type'] = 'Nessus'
        return context

    def get_success_url(self):
        return reverse_lazy('reports:report_list', kwargs={
            'customer_id': self.request.selected_customer.customer_id,
            'service_id': self.object.service.service_id
        })

class NessusReportDeleteView(ReportDeleteView):
    model = NessusReport
    permission_required = 'reports.delete_nessusreport'