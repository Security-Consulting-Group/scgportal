from django.urls import path
from .views import UserListView, UserCreateView, UserUpdateView, UserActivateView, UserDeactivateView, UserResetPasswordView

app_name = 'users'

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('create/', UserCreateView.as_view(), name='user-create'),
    path('<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('<int:pk>/activate/', UserActivateView.as_view(), name='user-activate'),
    path('<int:pk>/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'),
    path('<int:pk>/reset-password/', UserResetPasswordView.as_view(), name='reset-user-password'),
]