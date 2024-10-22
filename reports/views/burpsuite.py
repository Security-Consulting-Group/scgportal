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
import json
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

class BurpSuiteReportDetailView(ReportDetailView):
    model = BurpSuiteReport
    template_name = 'reports/burpsuite/report_detail.html'
    context_object_name = 'report'
    permission_required = 'reports.view_burpsuitereport'
    
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
                    'severity_counts': {'High': 0, 'Medium': 0, 'Low': 0, 'Information': 0}  # Initialize counts
                }
            
            instance_data = {
                'path': vuln.path,
                'location': vuln.location,
                'severity': vuln.severity,
                'confidence': vuln.confidence,
                'issueDetail': vuln.issueDetail,
                'requests': json.loads(vuln.request)
            }
            grouped_vulnerabilities[signature_id]['instances'].append(instance_data)
            # Increment the severity counter
            grouped_vulnerabilities[signature_id]['severity_counts'][vuln.severity] += 1
        
        context['issues'] = list(grouped_vulnerabilities.values())
        return context


class BurpSuiteReportUploadView(ReportBaseView, FormView):
    form_class = BurpSuiteReportUploadForm
    template_name = 'reports/report_upload.html'
    permission_required = 'reports.add_burpsuitereport'

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