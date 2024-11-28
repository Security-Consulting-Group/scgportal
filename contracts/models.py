from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from customers.models import Customer
from inventories.models import Service
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class Contract(models.Model):
    CONTRACT_STATUS_CHOICES = [
        ('TRIAL', 'Trial'),
        ('NOTSTARTED', 'Not Started'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    contract_id = models.CharField(max_length=50, primary_key=True, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, to_field='customer_id')
    contract_start_date = models.DateField()
    contract_end_date = models.DateField()
    contract_status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default='NOTSTARTED')
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    discount = models.DecimalField(_('Global Discount (%)'), max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    taxes = models.DecimalField(_('Taxes (%)'), max_digits=5, decimal_places=2, default=13.00, validators=[MinValueValidator(0), MaxValueValidator(100)])
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    services = models.ManyToManyField(Service, through='ContractService')
    contract_notes = models.TextField(blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def clean(self):
        if self.contract_start_date and self.customer and self.contract_start_date < self.customer.created_on.date():
            raise ValidationError("Contract start date cannot be before customer creation date.")
        if self.contract_end_date and self.contract_start_date and self.contract_end_date < self.contract_start_date:
            raise ValidationError("Contract end date cannot be before start date.")

    def delete(self, *args, **kwargs):
        # Disconnect any virtual reports before deletion
        try:
            from reports.models import SupportReport
            SupportReport.objects.filter(contract=self).update(contract=None)
        except:
            pass  # If table doesn't exist, continue with deletion
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.contract_id:
            now = timezone.now()
            self.contract_id = now.strftime("C-%Y%m%d-%H%M%S")
        self.clean()
        super().save(*args, **kwargs)
        self.calculate_total()

    def calculate_total(self):
        self.sub_total = Decimal('0')
        for cs in self.contractservice_set.all():
            service_subtotal = cs.service.service_price * cs.quantity
            if cs.discount:
                service_subtotal -= service_subtotal * (cs.discount / 100)
            else:
                service_subtotal -= service_subtotal * (self.discount / 100) if self.discount else Decimal('0')
            self.sub_total += service_subtotal

        tax_amount = self.sub_total * (self.taxes / 100)
        self.total = self.sub_total + tax_amount

        # Calculate the total payments made
        total_payments = sum(payment.amount for payment in self.payments.all())

        # Update the balance
        self.balance = self.total - total_payments

        # Use update() to avoid triggering the save() method again
        Contract.objects.filter(pk=self.pk).update(
            sub_total=self.sub_total,
            total=self.total,
            balance=self.balance
        )
        
    def get_services_data(self):
        return ','.join([f"{service.id}:{service.service_name}" for service in self.services.all()])
        
    class Meta:
        # Add this to ensure Django knows the field type has changed
        constraints = [
            models.UniqueConstraint(fields=['customer', 'contract_id'], name='unique_contract_per_customer')
        ]
        
    @property
    def taxes_amount(self):
        return self.sub_total * (self.taxes / Decimal('100'))

    def __str__(self):
        return self.contract_id

class ContractService(models.Model):
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE, to_field='contract_id')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    discount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        unique_together = ('contract', 'service')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contract.calculate_total()

    def __str__(self):
        return f"{self.contract.contract_id} - {self.service.service_name} (Qty: {self.quantity})"