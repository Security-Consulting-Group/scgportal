from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag(takes_context=True)
def dashboard_url(context):
    request = context['request']
    user = request.user
    
    if user.is_authenticated:
        if user.type in [user.UserType.MULTI_ACCOUNT, user.UserType.STAFF]:
            return reverse('customers:customer-list')
        else:
            selected_customer = getattr(request, 'selected_customer', None)
            if selected_customer:
                return reverse('dashboard:dashboard', kwargs={'customer_id': selected_customer.customer_id})
    
    # Fallback to the root URL if no conditions are met
    return reverse('root')