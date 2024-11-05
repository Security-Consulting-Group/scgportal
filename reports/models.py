from django.db import models
from django.contrib.auth import get_user_model
from customers.models import Customer
from django.conf import settings
from inventories.models import Service
from signatures.models import NessusSignature, BurpSuiteSignature
import uuid

class BaseReport(models.Model):
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, to_field='customer_id')
    contract = models.ForeignKey('contracts.Contract', on_delete=models.CASCADE, null=True, blank=True, to_field='contract_id')
    date = models.DateField(auto_now_add=True)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    
    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.name} - {self.customer.customer_name} - {self.date}"

class NessusReport(BaseReport):
    inventory = models.JSONField()

class NessusVulnerability(models.Model):
    report = models.ForeignKey(NessusReport, on_delete=models.CASCADE, related_name='vulnerabilities')
    signature = models.ForeignKey(NessusSignature, on_delete=models.CASCADE)
    target_affected = models.CharField(max_length=255)
    operating_system = models.CharField(max_length=255)
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_review', 'In Review'),
        ('monitoring', 'Monitoring'),
        ('mitigated', 'Mitigated'),
        ('fixed', 'Fixed'),
        ('risk_accepted', 'Risk Accepted'),
        ('not_applicable', 'Not Applicable'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    changed_at = models.DateTimeField(auto_now=True)
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.signature} - {self.target_affected} - {self.status}"

class BurpSuiteReport(BaseReport):
    pass

class BurpSuiteVulnerability(models.Model):
    report = models.ForeignKey(BurpSuiteReport, on_delete=models.CASCADE, related_name='vulnerabilities')
    signature = models.ForeignKey(BurpSuiteSignature, on_delete=models.CASCADE)
    host = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    severity = models.CharField(max_length=50)
    confidence = models.CharField(max_length=50)
    issueDetail = models.TextField(default='N/A', null=False)
    request = models.TextField()

    def __str__(self):
        return f"{self.signature} - {self.host} - {self.severity}"

class SupportReport(BaseReport):
    """Virtual report type to show engagement data"""
    class Meta:
        managed = False  # This ensures Django won't create a DB table
        default_permissions = ('view',)  # Only allow viewing

    @classmethod
    def generate_for_service(cls, service, customer):
        """Generate a virtual report from engagements data"""
        from engagements.models import Engagement, TimeEntry
        
        total_hours = TimeEntry.objects.filter(
            engagement__contract_service__service=service,
            engagement__customer=customer
        ).aggregate(total=models.Sum('hours_spent'))['total'] or Decimal('0')
        
        engagement_stats = Engagement.objects.filter(
            contract_service__service=service,
            customer=customer
        ).aggregate(
            open_count=models.Count('pk', filter=models.Q(status='OPEN')),
            in_progress_count=models.Count('pk', filter=models.Q(status='IN_PROGRESS')),
            resolved_count=models.Count('pk', filter=models.Q(status='RESOLVED')),
            cancelled_count=models.Count('pk', filter=models.Q(status='CANCELLED')),
        )
        
        return {
            'total_hours': total_hours,
            'stats': engagement_stats,
        }