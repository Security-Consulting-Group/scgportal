from django.db import models
from customers.models import Customer
from contracts.models import Contract
from signatures.models import Signature
from services.models import Service
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

import uuid

class SecurityReport(models.Model):
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, to_field='customer_id')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True, blank=True, to_field='contract_id')
    scan_date = models.DateField()
    inventory = models.JSONField()
    report_type = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        contract_info = f"Contract {self.contract.contract_id}" if self.contract else "No Contract"
        return f"Report {self.report_id} for {self.customer.customer_name} - {contract_info}"

class ReportVulnerability(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_review', 'In Review'),
        ('monitoring', 'Monitoring'),
        ('mitigated', 'Mitigated'),
        ('fixed', 'Fixed'),
        ('accepted', 'Accepted'),
    ]

    report = models.ForeignKey(SecurityReport, on_delete=models.CASCADE, related_name='vulnerabilities')
    signature = models.ForeignKey(Signature, on_delete=models.CASCADE)
    target_affected = models.CharField(max_length=255, default='Unknown')
    operating_system = models.CharField(max_length=255, default='Unknown')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')

    def __str__(self):
        return f"{self.signature.plugin_name} on {self.target_affected} - {self.get_status_display()}"

class VulnerabilityHistory(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, to_field='customer_id')
    signature = models.ForeignKey(Signature, on_delete=models.CASCADE)
    target_affected = models.CharField(max_length=255)
    report = models.ForeignKey(SecurityReport, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ReportVulnerability.STATUS_CHOICES)
    detected_date = models.DateField()
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('customer', 'signature', 'target_affected', 'report')
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.signature.plugin_name} on {self.target_affected} for {self.customer.customer_name} in report {self.report.report_id}"