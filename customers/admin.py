from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'customer_name', 'customer_type', 'created_on')
    readonly_fields = ('customer_id', 'created_on')
    search_fields = ('customer_id', 'customer_name')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('customer_id',)
        return self.readonly_fields