from django.db import models
from django.utils import timezone

class Signature(models.Model):
    RISK_FACTOR_CHOICES = [
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
        ('Informational', 'Informational'),
    ]
    SCANNER_CHOICES = [
        ('Nessus', 'Nessus'),
    ]

    id = models.IntegerField(primary_key=True)
    plugin_name = models.CharField(max_length=1000)
    exploitability_ease = models.CharField(max_length=255, null=True, blank=True)
    cpe = models.TextField(null=True, blank=True)
    solution = models.TextField(null=True, blank=True)
    risk_factor = models.CharField(max_length=20, choices=RISK_FACTOR_CHOICES)
    description = models.TextField(null=True, blank=True)
    cvss_vector = models.CharField(max_length=255, null=True, blank=True)
    synopsis = models.TextField(null=True, blank=True)
    see_also = models.TextField(null=True, blank=True)
    plugin_modification_date = models.DateField(null=True, blank=True)
    cvss_base_score = models.FloatField(null=True, blank=True)
    cve = models.TextField(null=True, blank=True)  # Store as JSON string
    vpr_score = models.FloatField(null=True, blank=True)
    exploit_code_maturity = models.CharField(max_length=50, null=True, blank=True)
    epss_score = models.FloatField(null=True, blank=True)
    family_name = models.CharField(max_length=255, null=True, blank=True)
    scanner_type = models.CharField(max_length=50, choices=SCANNER_CHOICES, default='Nessus')
    scg_last_update = models.DateTimeField(default=timezone.now)
    agent = models.TextField(null=True, blank=True)
    cvss3_base_score = models.FloatField(null=True, blank=True)
    cvss3_vector = models.CharField(max_length=255, null=True, blank=True)
    xref = models.TextField(null=True, blank=True)  # Store as JSON string

    class Meta:
        ordering = ['id'] 

    def __str__(self):
        return f"{self.id} - {self.plugin_name}"