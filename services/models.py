from django.db import models

class Service(models.Model):
    service_id = models.CharField(max_length=50, unique=True)
    service_name = models.CharField(max_length=100)
    service_description = models.TextField(blank=True)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.service_name