from django.db import models
from contracts.models import Contract
from decimal import Decimal

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEPOSIT', 'Deposit'),
        ('OTHER', 'Other'),
    ]

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    invoice_number = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_contract_balance()

    def update_contract_balance(self):
        total_paid = sum(payment.amount for payment in self.contract.payments.all())
        self.contract.balance = self.contract.total - total_paid
        self.contract.save()

    def __str__(self):
        return f"Payment {self.invoice_number} for Contract {self.contract.contract_id}"