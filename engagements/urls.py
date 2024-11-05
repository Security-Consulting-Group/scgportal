# engagements/urls.py
from django.urls import path
from .views import (
    EngagementListView,
    EngagementCreateView,
    EngagementDetailView,
    EngagementUpdateView,
    EngagementStatusUpdateView,
    TimeEntryCreateView,
    TimeEntryUpdateView,
)

app_name = 'engagements'

urlpatterns = [
    path('', EngagementListView.as_view(), name='engagement-list'),
    path('create/', EngagementCreateView.as_view(), name='engagement-create'),
    path('<str:engagement_id>/', EngagementDetailView.as_view(), name='engagement-detail'),
    path('<str:engagement_id>/update/', EngagementUpdateView.as_view(), name='engagement-update'),
    
    # Time Entry URLs
    path('<str:engagement_id>/time-entry/create/', 
         TimeEntryCreateView.as_view(), name='time-entry-create'),
    path('<str:engagement_id>/time-entry/<int:pk>/update/', 
         TimeEntryUpdateView.as_view(), name='time-entry-update'),

    path('<str:engagement_id>/status/', 
        EngagementStatusUpdateView.as_view(), 
        name='engagement-status-update'),
]