from django.urls import path
from .views import SecurityReportListView, SecurityReportDetailView, SecurityReportDeleteView, UploadReportView

app_name = 'sec_reports'

urlpatterns = [
    path('', SecurityReportListView.as_view(), name='report-list'),
    path('<uuid:report_id>/', SecurityReportDetailView.as_view(), name='report_detail'),
    path('<uuid:report_id>/update_status/', SecurityReportDetailView.as_view(), name='update_vulnerability_status'),
    path('<uuid:report_id>/delete/', SecurityReportDeleteView.as_view(), name='report_delete'),
    path('upload/', UploadReportView.as_view(), name='upload_report'),
]