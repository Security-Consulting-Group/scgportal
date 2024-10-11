from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from customers.models import Customer

class SelectedCustomerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        selected_customer = self.get_selected_customer()
        if self.request.user.is_staff:
            return True
        return selected_customer in self.request.user.customers.all()

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You do not have permission to access this customer's data.")
        return super().handle_no_permission()

    def get_selected_customer(self):
        customer_id = self.kwargs.get('customer_id')
        return get_object_or_404(Customer, customer_id=customer_id)

    def dispatch(self, request, *args, **kwargs):
        # Set selected_customer as an attribute of the view instance
        self.selected_customer = self.get_selected_customer()
        # Also set it on the request for backward compatibility
        request.selected_customer = self.selected_customer
        return super().dispatch(request, *args, **kwargs)