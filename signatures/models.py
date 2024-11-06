from django.db import models
from django.utils import timezone

class BaseSignature(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=1000)
    description = models.TextField(null=True, blank=True)
    scanner_type = models.CharField(max_length=50)
    scg_last_update = models.DateTimeField(default=timezone.now)
    references = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['id']

    def __str__(self):
        return f"{self.id} - {self.name}"

class NessusSignature(BaseSignature):
    RISK_FACTOR_CHOICES = [
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
        ('Informational', 'Informational'),
    ]
    
    exploitability_ease = models.CharField(max_length=255, null=True, blank=True)
    cpe = models.TextField(null=True, blank=True)
    solution = models.TextField(null=True, blank=True)
    risk_factor = models.CharField(max_length=20, choices=RISK_FACTOR_CHOICES)
    cvss_vector = models.CharField(max_length=255, null=True, blank=True)
    synopsis = models.TextField(null=True, blank=True)
    plugin_modification_date = models.DateField(null=True, blank=True)
    cvss_base_score = models.FloatField(null=True, blank=True)
    cve = models.TextField(null=True, blank=True)
    vpr_score = models.FloatField(null=True, blank=True)
    exploit_code_maturity = models.CharField(max_length=50, null=True, blank=True)
    epss_score = models.FloatField(null=True, blank=True)
    family_name = models.CharField(max_length=255, null=True, blank=True)
    agent = models.TextField(null=True, blank=True)
    cvss3_base_score = models.FloatField(null=True, blank=True)
    cvss3_vector = models.CharField(max_length=255, null=True, blank=True)
    xref = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.scanner_type = 'Nessus'
        super().save(*args, **kwargs)

class BurpSuiteSignature(BaseSignature):
    remediation = models.TextField(null=True, blank=True)
    vulnerability_classifications = models.TextField(null=True, blank=True)
    retired = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.scanner_type = 'BurpSuite'
        super().save(*args, **kwargs)