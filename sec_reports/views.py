from django.views.generic import ListView, DetailView, DeleteView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.mixins import SelectedCustomerRequiredMixin
from .forms import ReportUploadForm
from .models import SecurityReport, ReportVulnerability, VulnerabilityHistory
from signatures.models import Signature
from customers.models import Customer
from contracts.models import Contract
from services.models import Service
import json, uuid
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from collections import defaultdict
from django.db import models
from django.db.models import Max
from django.contrib.auth import get_user_model
from django.utils import timezone

class SecurityReportListView(SelectedCustomerRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'sec_reports.view_securityreport'
    model = SecurityReport
    template_name = 'sec_reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    ordering = ['-scan_date']

    def get_queryset(self):
        return SecurityReport.objects.filter(customer=self.request.selected_customer).order_by('-scan_date')

class SecurityReportDetailView(SelectedCustomerRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = SecurityReport
    template_name = 'sec_reports/report_detail.html'
    context_object_name = 'report'
    permission_required = 'sec_reports.view_securityreport'

    def get_object(self, queryset=None):
        report_id = self.kwargs.get('report_id')
        return get_object_or_404(SecurityReport, report_id=report_id, customer=self.request.selected_customer)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vulnerabilities = self.object.vulnerabilities.select_related('signature').all()
        
        # Fetch the latest change information for each vulnerability
        latest_changes = VulnerabilityHistory.objects.filter(
            report=self.object
        ).values(
            'signature', 'target_affected'
        ).annotate(
            latest_change=Max('changed_at'),
            changed_by_id=models.F('changed_by')
        )

        # Create a dictionary to store the latest change info
        latest_changes_dict = {
            (change['signature'], change['target_affected']): (change['latest_change'], change['changed_by_id'])
            for change in latest_changes
        }

        # Fetch user information separately
        user_dict = dict(get_user_model().objects.filter(
            vulnerabilityhistory__report=self.object
        ).values_list('id', 'email'))

        def severity_order(risk_factor):
            order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'None': 4}
            return order.get(risk_factor, 5)
        
        grouped_vulnerabilities = defaultdict(lambda: defaultdict(list))

        for vuln in vulnerabilities:
            if vuln.signature.see_also:
                vuln.signature.see_also = vuln.signature.see_also.split()
            if vuln.signature.cve:
                try:
                    cve_list = json.loads(vuln.signature.cve)
                    vuln.signature.cve = [cve.strip() for cve in cve_list if cve.strip()]
                except json.JSONDecodeError:
                    vuln.signature.cve = []
            
            # Add latest change information
            latest_change_info = latest_changes_dict.get((vuln.signature.id, vuln.target_affected))
            if latest_change_info and latest_change_info[0]:  # Check if changed_at is not None
                vuln.latest_change = latest_change_info[0]
                vuln.changed_by = user_dict.get(latest_change_info[1], 'N/A')
            else:
                vuln.latest_change = 'N/A'
                vuln.changed_by = 'N/A'
            
            # Group vulnerabilities
            grouped_vulnerabilities[vuln.signature.risk_factor][vuln.signature.id].append(vuln)
        
        sorted_vulnerabilities = []
        for risk_factor in sorted(grouped_vulnerabilities.keys(), key=severity_order):
            vuln_group = {
                'risk_factor': risk_factor,
                'vulnerabilities': []
            }
            for signature_id, vulns in grouped_vulnerabilities[risk_factor].items():
                vuln_group['vulnerabilities'].append({
                    'signature': vulns[0].signature,
                    'targets': vulns
                })
            sorted_vulnerabilities.append(vuln_group)
        
        context['grouped_vulnerabilities'] = sorted_vulnerabilities
        return context

    @method_decorator(require_POST)
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
                    vulnerabilities = ReportVulnerability.objects.filter(
                        report=report,
                        signature_id=ReportVulnerability.objects.get(id=vulnerability_id).signature_id
                    )
                elif bulk_type == 'risk_factor':
                    vulnerabilities = ReportVulnerability.objects.filter(
                        report=report,
                        signature__risk_factor=risk_factor
                    )
                else:
                    vulnerabilities = ReportVulnerability.objects.filter(id=vulnerability_id, report=report)

                current_time = timezone.now()
                for vulnerability in vulnerabilities:
                    if vulnerability.status != new_status:
                        vulnerability.status = new_status
                        vulnerability.save()

                        # Use update_or_create instead of create
                        history, created = VulnerabilityHistory.objects.update_or_create(
                            customer=report.customer,
                            signature=vulnerability.signature,
                            target_affected=vulnerability.target_affected,
                            report=report,
                            defaults={
                                'status': new_status,
                                'detected_date': report.scan_date,
                                'changed_by': request.user,
                            }
                        )

                        updated_vulnerabilities.append({
                            'id': vulnerability.id,
                            'target_affected': vulnerability.target_affected,
                            'status': new_status,
                            'changed_by': request.user.email,
                            'changed_at': history.changed_at.isoformat()
                        })

                return JsonResponse({
                    'success': True, 
                    'new_status': dict(ReportVulnerability.STATUS_CHOICES)[new_status],
                    'updated_count': len(updated_vulnerabilities),
                    'updated_vulnerabilities': updated_vulnerabilities,
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    def post(self, request, *args, **kwargs):
        return self.update_vulnerability_status(request, *args, **kwargs)

class SecurityReportDeleteView(SelectedCustomerRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'sec_reports.delete_securityreport'
    model = SecurityReport
    template_name = 'sec_reports/report_confirm_delete.html'
    context_object_name = 'report'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            report_id=self.kwargs['report_id'],
            customer__customer_id=self.kwargs['customer_id']
        )

    def get_success_url(self):
        return reverse_lazy('sec_reports:report-list', kwargs={
            'customer_id': self.object.customer.customer_id
        })

class UploadReportView(SelectedCustomerRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, FormView):
    form_class = ReportUploadForm
    template_name = 'sec_reports/upload_report.html'
    permission_required = 'sec_reports.add_securityreport'

    def get_success_url(self):
        return reverse_lazy('sec_reports:report-list', kwargs={
            'customer_id': self.request.selected_customer.customer_id
        })

    def get_initial(self):
        initial = super().get_initial()
        customer_id = self.request.GET.get('customer')
        if customer_id:
            initial['customer'] = get_object_or_404(Customer, customer_id=customer_id)
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['customer'] = self.request.selected_customer
        return kwargs

    def get(self, request, *args, **kwargs):
        if 'contract_id' in request.GET:
            return self.get_services_for_contract(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_services_for_contract(self, request, *args, **kwargs):
        contract_id = request.GET.get('contract_id')
        services = []
        if contract_id:
            services = list(Service.objects.filter(contractservice__contract__contract_id=contract_id).distinct().values('id', 'service_name'))
        return JsonResponse({'services': services})

    def form_valid(self, form):
        customer = form.customer
        json_file = form.cleaned_data['json_file']
        contract = form.cleaned_data.get('contract')
        report_type = form.cleaned_data.get('report_type')
        try:
            data = json.load(json_file)

            with transaction.atomic():
                self.security_report = SecurityReport.objects.create(
                    customer=self.request.selected_customer,
                    contract=contract,
                    scan_date=data['scan_date'],
                    inventory=data['inventory'],
                    report_type=report_type
                )

                for alert in data['alert_report']:
                    try:
                        signature = Signature.objects.get(id=alert['plugin_id'])

                        vulnerability, created = ReportVulnerability.objects.get_or_create(
                            report=self.security_report,
                            signature=signature,
                            target_affected=alert['target_affected'],
                            defaults={
                                'operating_system': alert['os'],
                                'status': 'not_started'
                            }
                        )

                        VulnerabilityHistory.objects.update_or_create(
                            customer=customer,
                            signature=signature,
                            target_affected=alert['target_affected'],
                            report=self.security_report,
                            defaults={
                                'status': vulnerability.status,
                                'detected_date': self.security_report.scan_date
                            }
                        )

                    except Signature.DoesNotExist:
                        messages.warning(self.request, f"Signature with ID {alert['plugin_id']} not found.")
                    except IntegrityError as e:
                        messages.warning(self.request, f"Duplicate entry skipped: {str(e)}")

                messages.success(self.request, f'Report {self.security_report.report_id} uploaded successfully.')

        except Exception as e:
            messages.error(self.request, f'Error uploading report: {str(e)}')
            print(f"Error uploading report: {str(e)}")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error uploading report. Please check the form and try again.')
        return super().form_invalid(form)