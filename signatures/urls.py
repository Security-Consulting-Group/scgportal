from django.urls import path
from .views import factory

app_name = 'signatures'

urlpatterns = [
    path('', factory.signature_selection_view, name='signature_selection'),
    path('<str:scanner_type>/', factory.signature_list_view, name='signature_list'),
    path('<str:scanner_type>/<int:pk>/', factory.signature_detail_view, name='signature_detail'),
    path('<str:scanner_type>/create/', factory.signature_create_view, name='signature_create'),
    path('<str:scanner_type>/<int:pk>/update/', factory.signature_update_view, name='signature_update'),
    path('<str:scanner_type>/<int:pk>/delete/', factory.signature_delete_view, name='signature_delete'),
]