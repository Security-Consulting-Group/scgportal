from django.urls import path
from .views import PaymentCreateView, PaymentListView, PaymentDetailView

app_name = 'payments'

urlpatterns = [
    path('contract/<str:contract_id>/payments/', PaymentListView.as_view(), name='payment-list'),
    path('contract/<str:contract_id>/create/', PaymentCreateView.as_view(), name='payment-create'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
]