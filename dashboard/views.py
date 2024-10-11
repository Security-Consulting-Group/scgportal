from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import SelectedCustomerRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse

class DashboardView(SelectedCustomerRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_customer'] = self.selected_customer
        return context

class DashboardRedirectView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.type in [user.UserType.MULTI_ACCOUNT, user.UserType.STAFF]:
            return reverse('customers:customer-list')
        else:
            default_customer = user.get_default_customer()
            if default_customer:
                return reverse('dashboard:dashboard', kwargs={'customer_id': default_customer.customer_id})
        return reverse('login')  # Fallback if no conditions are met