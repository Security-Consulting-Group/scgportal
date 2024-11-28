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

    def delete(self, *args, **kwargs):
        # Delete all contracts first
        from django.db import connection
        
        # Delete all contracts
        for contract in self.contract_set.all():
            # Delete contract services
            contract.contractservice_set.all().delete()
            contract.delete()
            
        # Execute raw SQL to clean up any potential references in other tables
        with connection.cursor() as cursor:
            tables = ['reports_nessusreport', 'reports_burpsuitereport']
            for table in tables:
                try:
                    cursor.execute(f"""
                        DELETE FROM "{table}" 
                        WHERE customer_id = %s
                    """, [str(self.customer_id)])
                except:
                    pass  # Table might not exist
                    
        # Finally delete the customer
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.customer_name

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
