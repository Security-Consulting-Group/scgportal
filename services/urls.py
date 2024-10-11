from django.urls import path
from .views import ServiceListView, ServiceDetailView, ServiceCreateView, ServiceUpdateView, ServiceDeleteView

app_name = 'services'

urlpatterns = [
    path('', ServiceListView.as_view(), name='service-list'),
    path('<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),
    path('create/', ServiceCreateView.as_view(), name='service-create'),
    path('<int:pk>/update/', ServiceUpdateView.as_view(), name='service-update'),
    path('<int:pk>/delete/', ServiceDeleteView.as_view(), name='service-delete'),
]