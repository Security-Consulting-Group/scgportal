from django.db import models
from django.conf import settings
from customers.models import Customer
from contracts.models import Contract, ContractService
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.contrib import messages

class Engagement(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CANCELLED', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    # Main fields
    engagement_id = models.CharField(max_length=50, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    priority = models.CharField(max_length=10,choices=PRIORITY_CHOICES,default='MEDIUM',db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,to_field='customer_id')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE,to_field='contract_id')
    contract_service = models.ForeignKey(ContractService,on_delete=models.CASCADE)
    # Descriptions
    client_description = models.TextField()
    internal_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='OPEN',db_index=True)
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='created_engagements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("view_internal_notes", "Can view internal notes"),
            # ("close_engagement", "Can close engagements"),
        ]

    def clean(self):
        if self.contract and not self.contract.contract_status == 'ACTIVE':
            raise ValidationError(_("Engagements can only be created for active contracts."))
        
        if self.contract and self.contract_service and self.contract_service.contract != self.contract:
            raise ValidationError(_("Selected service must belong to the selected contract."))
        
        if self.contract and self.customer and self.contract.customer != self.customer:
            raise ValidationError(_("Contract must belong to the selected customer."))

    @property
    def priority_label(self):
        """Returns bootstrap class for priority badge"""
        return {
            'LOW': 'badge bg-success',
            'MEDIUM': 'badge bg-info',
            'HIGH': 'badge bg-warning',
            'URGENT': 'badge bg-danger',
        }.get(self.priority, 'badge bg-secondary')

    @property
    def total_service_hours(self):
        """Get total hours used across all engagements for this contract service"""
        return TimeEntry.objects.filter(
            engagement__contract_service=self.contract_service
        ).aggregate(
            total=models.Sum('hours_spent')
        )['total'] or Decimal('0')

    @property
    def remaining_service_hours(self):
        """Get remaining hours for this contract service"""
        contracted_hours = self.contract_service.quantity
        return contracted_hours - self.total_service_hours

    @property
    def service_hours_percentage(self):
        """Calculate percentage of used hours for this contract service"""
        if self.contract_service.quantity > 0:
            return (self.total_service_hours / self.contract_service.quantity) * 100
        return 0

    @property
    def engagement_hours(self):
        """Get total hours used for this specific engagement"""
        return self.timeentry_set.aggregate(
            total=models.Sum('hours_spent')
        )['total'] or Decimal('0')

    @property
    def engagement_hours_percentage(self):
        """Calculate percentage of used hours for this specific engagement"""
        if self.contract_service.quantity > 0:
            return (self.engagement_hours / self.contract_service.quantity) * 100
        return 0

    def save(self, *args, **kwargs):
        if not self.engagement_id:
            # Get the last engagement number
            last_engagement = Engagement.objects.order_by('-engagement_id').first()
            if last_engagement and last_engagement.engagement_id[4:].isdigit():
                last_number = int(last_engagement.engagement_id[4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.engagement_id = f'EFF-{new_number:04d}'
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.engagement_id} - {self.name}"

class TimeEntry(models.Model):
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE)
    client_comment = models.TextField(
        help_text=_("Comment visible to the client about the work done")
    )
    internal_notes = models.TextField(
        help_text=_("Internal notes about the work - only visible to staff"),
        blank=True
    )
    hours_spent = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        help_text=_("Number of hours spent on this work")
    )
    date = models.DateField()
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_timeentries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Time entries'

    def clean(self):
        total_hours = TimeEntry.objects.filter(
            engagement__contract_service=self.engagement.contract_service
        ).aggregate(
            total=models.Sum('hours_spent')
        )['total'] or Decimal('0')
        
        # Add current hours
        total_hours += self.hours_spent
        contracted_hours = self.engagement.contract_service.quantity
        
        # Instead of using messages, just set a warning attribute that the view can use
        if total_hours > contracted_hours:
            self.hours_warning = _(
                f"This entry will exceed the contracted hours. "
                f"Contracted: {contracted_hours}h, "
                f"Total used: {total_hours - self.hours_spent}h, "
                f"This entry: {self.hours_spent}h"
            )

    def __str__(self):
        return f"Time entry for {self.engagement.name} - {self.date}"