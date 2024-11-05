from django.contrib import admin
from .models import Engagement, TimeEntry

@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ['name', 'customer', 'contract_service', 'status', 'priority', 'created_by', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['name', 'client_description']
    raw_id_fields = ['customer', 'contract', 'contract_service', 'created_by']

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['engagement', 'hours_spent', 'date', 'created_by', 'created_at']
    list_filter = ['date', 'created_at']
    raw_id_fields = ['engagement', 'created_by']