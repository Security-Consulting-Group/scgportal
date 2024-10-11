from django.shortcuts import get_object_or_404
from customers.models import Customer
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
import uuid

class CustomerSelectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Only set the default customer if one isn't already selected
            if not hasattr(request, 'selected_customer'):
                selected_customer_id = request.session.get('selected_customer_id')
                
                if selected_customer_id:
                    try:
                        # Convert string back to UUID
                        uuid_customer_id = uuid.UUID(selected_customer_id)
                        request.selected_customer = Customer.objects.get(customer_id=uuid_customer_id)
                    except (ValueError, Customer.DoesNotExist):
                        request.selected_customer = None
                        del request.session['selected_customer_id']
                
                if not hasattr(request, 'selected_customer') or request.selected_customer is None:
                    # If no customer is selected, get the default customer
                    default_customer = request.user.get_default_customer()
                    if default_customer:
                        request.selected_customer = default_customer
                        # Convert UUID to string before storing in session
                        request.session['selected_customer_id'] = str(default_customer.customer_id)
                    else:
                        request.selected_customer = None

        response = self.get_response(request)
        return response