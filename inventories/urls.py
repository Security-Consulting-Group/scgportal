from django.urls import path
from . import views

app_name = 'inventories'

urlpatterns = [
    path('', views.InventorySelectionView.as_view(), name='inventory_selection'),

    # Service URLs
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('services/create/', views.ServiceCreateView.as_view(), name='service_create'),
    path('services/<int:pk>/update/', views.ServiceUpdateView.as_view(), name='service_update'),

    # ReportType URLs
    path('reporttypes/', views.ReportTypeListView.as_view(), name='reporttype_list'),
    path('reporttypes/<int:pk>/', views.ReportTypeDetailView.as_view(), name='reporttype_detail'),
    path('reporttypes/create/', views.ReportTypeCreateView.as_view(), name='reporttype_create'),
    path('reporttypes/<int:pk>/update/', views.ReportTypeUpdateView.as_view(), name='reporttype_update'),
    path('reporttypes/<int:pk>/delete/', views.ReportTypeDeleteView.as_view(), name='reporttype_delete'),
]