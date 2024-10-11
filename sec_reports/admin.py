from django.contrib import admin
from .models import SecurityReport, ReportVulnerability, VulnerabilityHistory

class ReportVulnerabilityInline(admin.TabularInline):
    model = ReportVulnerability
    extra = 1
    raw_id_fields = ['signature']

@admin.register(SecurityReport)
class SecurityReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'customer', 'contract', 'scan_date', 'report_type')
    list_filter = ('scan_date', 'report_type', 'customer')
    search_fields = ('report_id', 'customer__customer_name', 'contract__contract_id')
    raw_id_fields = ['customer', 'contract', 'report_type']
    inlines = [ReportVulnerabilityInline]

@admin.register(ReportVulnerability)
class ReportVulnerabilityAdmin(admin.ModelAdmin):
    list_display = ('signature', 'target_affected', 'operating_system', 'status', 'report')
    list_filter = ('status', 'operating_system')
    search_fields = ('signature__plugin_name', 'target_affected', 'report__report_id')
    raw_id_fields = ['report', 'signature']

@admin.register(VulnerabilityHistory)
class VulnerabilityHistoryAdmin(admin.ModelAdmin):
    list_display = ('customer', 'signature', 'target_affected', 'report', 'status', 'detected_date', 'changed_by', 'changed_at')
    list_filter = ('status', 'detected_date', 'changed_at', 'customer')
    search_fields = ('customer__customer_name', 'signature__plugin_name', 'target_affected', 'report__report_id')
    raw_id_fields = ['customer', 'signature', 'report', 'changed_by']
    readonly_fields = ('changed_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'signature', 'report', 'changed_by')