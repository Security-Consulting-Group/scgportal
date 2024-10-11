from django.urls import path
from .views import ContractListView, ContractDetailView, ContractCreateView, ContractUpdateView, ContractDeleteView

app_name = 'contracts'

urlpatterns = [
    path('', ContractListView.as_view(), name='contract-list'),
    path('create/', ContractCreateView.as_view(), name='contract-create'),
    path('<str:contract_id>/update/', ContractUpdateView.as_view(), name='contract-update'),
    path('<str:contract_id>/delete/', ContractDeleteView.as_view(), name='contract-delete'),
    path('<str:contract_id>/', ContractDetailView.as_view(), name='contract-detail'),
]