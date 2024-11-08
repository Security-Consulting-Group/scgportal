from django.contrib import admin
from .models import Service, ReportType

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_id', 'service_name', 'service_price', 'is_active', 'report_type')
    list_filter = ('is_active', 'report_type')
    search_fields = ('service_id', 'service_name')

@admin.register(ReportType)
class ReportTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)