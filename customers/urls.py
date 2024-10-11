from django.urls import path
from .views import (
    CustomerListView,
    CustomerDetailView,
    CustomerCreateView,
    CustomerUpdateView,
    CustomerDeleteView,
)

app_name = 'customers'

urlpatterns = [
    path('', CustomerListView.as_view(), name='customer-list'),
    path('<uuid:pk>/', CustomerDetailView.as_view(), name='customer-detail'),
    path('create/', CustomerCreateView.as_view(), name='customer-create'),
    path('<uuid:pk>/update/', CustomerUpdateView.as_view(), name='customer-update'),
    path('<uuid:pk>/delete/', CustomerDeleteView.as_view(), name='customer-delete'),
]