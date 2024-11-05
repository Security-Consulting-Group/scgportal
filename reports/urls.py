from django.urls import path
from .views import factory

app_name = 'reports'

urlpatterns = [
    path('', factory.report_selection_view, name='report_selection'),
    path('<str:service_id>/', factory.report_list_view, name='report_list'),
    path('<str:service_id>/upload/', factory.report_upload_view, name='report_upload'),
    path('<str:service_id>/<uuid:pk>/', factory.report_detail_view, name='report_detail'),
    path('<str:service_id>/<uuid:pk>/delete/', factory.report_delete_view, name='report_delete'),
    path('<str:service_id>/<str:pk>/', factory.report_detail_view, name='support_report_detail'),
]