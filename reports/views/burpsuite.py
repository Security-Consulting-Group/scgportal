from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db import transaction
from django.shortcuts import get_object_or_404
from .base import ReportBaseView, ReportListView, ReportDetailView, ReportDeleteView
from ..models import BurpSuiteReport, BurpSuiteVulnerability
from ..forms.burpsuite import BurpSuiteReportUploadForm
from signatures.models import BurpSuiteSignature
from inventories.models import Service
from ..views.mixins import StatusSummaryMixin
import json
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError

class BurpSuiteReportListView(ReportListView):
    model = BurpSuiteReport
    template_name = 'reports/report_list.html'
    permission_required = 'reports.view_burpsuitereport'
    context_object_name = 'reports'

    def get_queryset(self):
        self.service = get_object_or_404(Service, service_id=self.kwargs['service_id'])
        return BurpSuiteReport.objects.filter(
            customer=self.request.selected_customer,
            service=self.service
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        return context

class BurpSuiteReportDetailView(StatusSummaryMixin, ReportDetailView):
    model = BurpSuiteReport
    template_name = 'reports/burpsuite/report_detail.html'
    permission_required = 'reports.view_burpsuitereport'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vulnerabilities = self.object.vulnerabilities.select_related('signature').all()
            
        status_summary = {}
        for status_value, status_label in BurpSuiteVulnerability.STATUS_CHOICES:
            count = vulnerabilities.filter(status=status_value).count()
            if count > 0:  # Only include statuses that have instances
                status_summary[status_label] = count
        
        context['status_summary'] = status_summary
        
        # Add STATUS_CHOICES to context
        context['STATUS_CHOICES'] = BurpSuiteVulnerability.STATUS_CHOICES
        
        grouped_vulnerabilities = {}
        for vuln in vulnerabilities:
            signature_id = vuln.signature.id
            if signature_id not in grouped_vulnerabilities:
                grouped_vulnerabilities[signature_id] = {
                    'type': signature_id,
                    'name': vuln.signature.name,
                    'host': vuln.host,
                    'signature': {
                        'description': vuln.signature.description,
                        'references': vuln.signature.references,
                        'remediation': vuln.signature.remediation,
                        'vulnerability_classifications': vuln.signature.vulnerability_classifications
                    },
                    'instances': [],
                    'severity_counts': {'High': 0, 'Medium': 0, 'Low': 0, 'Information': 0}
                }
            
            instance_data = {
                'id': vuln.id,  # Add this
                'path': vuln.path,
                'location': vuln.location,
                'severity': vuln.severity,
                'confidence': vuln.confidence,
                'issueDetail': vuln.issueDetail,
                'requests': json.loads(vuln.request),
                'status': vuln.status,  # Add this
                'changed_by': vuln.changed_by.email if vuln.changed_by else 'N/A',  # Add this
                'changed_at': timezone.localtime(vuln.changed_at).strftime('%b %d, %Y, %I:%M:%S %p') if vuln.changed_at else 'N/A',  # Add this
            }
            grouped_vulnerabilities[signature_id]['instances'].append(instance_data)
            grouped_vulnerabilities[signature_id]['severity_counts'][vuln.severity] += 1
        
        context['issues'] = list(grouped_vulnerabilities.values())
        return context

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        return self.update_vulnerability_status(request, *args, **kwargs)

    def update_vulnerability_status(self, request, *args, **kwargs):
        vulnerability_id = request.POST.get('vulnerability_id')
        new_status = request.POST.get('status')
        bulk_type = request.POST.get('bulk_type')
        severity = request.POST.get('severity')

        try:
            with transaction.atomic():
                report = self.get_object()
                updated_vulnerabilities = []

                if bulk_type == 'signature':
                    vulnerabilities = BurpSuiteVulnerability.objects.filter(
                        report=report,
                        signature_id=BurpSuiteVulnerability.objects.get(id=vulnerability_id).signature_id
                    )
                elif bulk_type == 'severity':
                    vulnerabilities = BurpSuiteVulnerability.objects.filter(
                        report=report,
                        severity=severity
                    )
                else:
                    vulnerabilities = BurpSuiteVulnerability.objects.filter(id=vulnerability_id, report=report)

                for vulnerability in vulnerabilities:
                    if vulnerability.status != new_status:
                        vulnerability.status = new_status
                        vulnerability.changed_by = request.user
                        vulnerability.save()

                        updated_vulnerabilities.append({
                            'id': vulnerability.id,
                            'status': new_status,
                            'changed_by': request.user.email,
                            'changed_at': timezone.localtime(vulnerability.changed_at).strftime('%b %d, %Y, %I:%M:%S %p')
                        })

                return JsonResponse({
                    'success': True, 
                    'new_status': dict(BurpSuiteVulnerability.STATUS_CHOICES)[new_status],
                    'updated_count': len(updated_vulnerabilities),
                    'updated_vulnerabilities': updated_vulnerabilities,
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

class BurpSuiteReportUploadView(ReportBaseView, FormView):
    form_class = BurpSuiteReportUploadForm
    template_name = 'reports/report_upload.html'
    permission_required = 'reports.add_burpsuitereport'

    def get(self, request, *args, **kwargs):
        # Handle AJAX request for services
        if 'contract_id' in request.GET:
            service = get_object_or_404(Service, service_id=self.kwargs['service_id'])
            services_data = [
                {'id': service.service_id, 'service_name': str(service)}
            ]
            return JsonResponse({'services': services_data})
            
        return super().get(request, *args, **kwargs)

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
                report = BurpSuiteReport.objects.create(
                    customer=self.request.selected_customer,
                    contract=contract,
                    service=service,
                    date=timezone.datetime.strptime(data['exportTime'], "%Y-%m-%d").date(),
                    name=report_name,
                )

                for issue in data['issues']:
                    signature, created = BurpSuiteSignature.objects.get_or_create(
                        id=issue['type'],
                        defaults={'name': issue['name']}
                    )
                    
                    for instance in issue['instances']:
                        required_fields = ['path', 'location', 'severity', 'confidence']
                        missing_fields = [field for field in required_fields if field not in instance or instance[field] is None]
                        
                        if missing_fields:
                            raise ValidationError(f"Required fields {', '.join(missing_fields)} are missing or null in the JSON data")

                        try:
                            BurpSuiteVulnerability.objects.create(
                                report=report,
                                signature=signature,
                                host=issue['host'],
                                path=instance['path'],
                                location=instance['location'],
                                severity=instance['severity'],
                                confidence=instance['confidence'],
                                issueDetail=instance.get('issueDetail') or 'N/A',  # Use 'N/A' if issueDetail is None or missing
                                request=json.dumps(instance.get('requests', []))
                            )
                        except Exception as e:
                            messages.error(self.request, f"Error creating BurpSuiteVulnerability: {str(e)}",
                            extra_tags='alert-danger')
                            raise

                messages.success(self.request,
                                mark_safe(f"BurpSuite Report <strong>{report.report_id}</strong> uploaded successfully."))

        except ValidationError as ve:
            messages.error(self.request,
                           mark_safe(f"Validation error: <strong>{str(ve)}</strong>"),
                           extra_tags='alert-danger')
            return self.form_invalid(form)
        except json.JSONDecodeError as je:
            messages.error(self.request,
                           mark_safe(f"Invalid JSON file: <strong>{str(je)}</strong>"),
                           extra_tags='alert-danger')
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
        context['report_type'] = 'BurpSuite'
        return context

    def get_success_url(self):
        return reverse_lazy('reports:report_list', kwargs={
            'customer_id': self.request.selected_customer.customer_id,
            'service_id': self.kwargs['service_id']
        })

class BurpSuiteReportDeleteView(ReportDeleteView):
    model = BurpSuiteReport
    permission_required = 'reports.delete_burpsuitereport'