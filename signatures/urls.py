from django.urls import path
from .views import SignatureListView, SignatureDetailView, SignatureCreateView, SignatureUpdateView, SignatureDeleteView, SignatureUploadView

app_name = 'signatures'

urlpatterns = [
    path('', SignatureListView.as_view(), name='signature_list'),
    path('<int:pk>/', SignatureDetailView.as_view(), name='signature_detail'),
    path('upload/', SignatureUploadView.as_view(), name='signature_upload'),
    path('create/', SignatureCreateView.as_view(), name='signature_create'),
    path('<int:pk>/update/', SignatureUpdateView.as_view(), name='signature_update'),
    path('<int:pk>/delete/', SignatureDeleteView.as_view(), name='signature_delete'),
]