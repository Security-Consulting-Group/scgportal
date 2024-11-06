from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from users.views import CustomLoginView, ProfileUpdateView, CustomPasswordResetConfirmView
from django.contrib.auth.decorators import login_required
from dashboard.views import DashboardRedirectView

urlpatterns = [
    path('', login_required(DashboardRedirectView.as_view()), name='root'),
    path('admin/', admin.site.urls),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # App-specific URLs
    path('accounts/', include('customers.urls'), name='customers'),
    path('inventories/', include('inventories.urls', namespace='inventories')),
    path('signatures/', include('signatures.urls'), name='signatures'),
    
    # Customer-specific paths
    path('<uuid:customer_id>/', include([
        path('dashboard/', include('dashboard.urls', namespace='dashboard')),
        path('contracts/', include('contracts.urls')),
        path('reports/', include('reports.urls')),
        path('payments/', include('payments.urls')),
        path('users/', include('users.urls')),
        path('engagements/', include('engagements.urls')),
    ])),
]