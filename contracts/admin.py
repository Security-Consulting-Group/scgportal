from django.contrib import admin
from .models import Contract, ContractService

class ContractServiceInline(admin.TabularInline):
    model = ContractService
    extra = 1

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_id', 'customer', 'contract_start_date', 'contract_end_date', 'contract_status', 'total')
    list_filter = ('contract_status', 'contract_start_date', 'contract_end_date')
    search_fields = ('contract_id', 'customer__customer_name')
    readonly_fields = ('contract_id', 'sub_total', 'total')
    inlines = [ContractServiceInline]
    fieldsets = (
        (None, {
            'fields': ('customer', 'contract_id', 'contract_start_date', 'contract_end_date', 'contract_status')
        }),
        ('Financial Details', {
            'fields': ('discount', 'taxes', 'sub_total', 'total')
        }),
        ('Additional Information', {
            'fields': ('contract_notes',)
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.save()
        obj.calculate_total()