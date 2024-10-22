from django.contrib import admin
from .models import NessusReport, BurpSuiteReport


@admin.register(NessusReport)
class NessusReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'customer', 'name', 'contract', 'service')
    list_filter = ('customer', 'contract', 'name', 'service')
    search_fields = ('customer', 'contract')
    readonly_fields = ('report_id',)
    fieldsets = (
        (None, {
            'fields': ('customer', 'name', 'contract', 'scan_date')
        }),
        ('Additional Information', {
            'fields': ('service',)
        }),
    )
    
@admin.register(BurpSuiteReport)
class BurpSuiteReportAdmin(admin.ModelAdmin):
    pass