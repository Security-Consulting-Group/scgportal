import uuid
from django.db import models

class Customer(models.Model):
    CUSTOMER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('main', 'Main'),
        ('reseller', 'Reseller'),
    ]
    
    customer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_name = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='customer')

    def __str__(self):
        return self.customer_name

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
