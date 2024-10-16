from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.mixins import SelectedCustomerRequiredMixin
from django.utils.safestring import mark_safe
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from customers.models import Customer
from customers.forms import CustomerForm

User = get_user_model()

class CustomerListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    permission_required = 'customers.view_customer'

    def get_queryset(self):
        return self.request.user.customers.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dashboard_url'] = reverse_lazy('dashboard:dashboard')
        return context

class CustomerDetailView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'
    permission_required = 'customers.view_customer'

    def get_object(self, queryset=None):
        # Use the `pk` from the URL to fetch the customer
        customer_id = self.kwargs.get('pk')
        return Customer.objects.get(customer_id=customer_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:customer-list')
    permission_required = 'customers.add_customer'

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Assign the customer to the user who created it
        self.request.user.customers.add(self.object)
        
        # Assign the customer to all superusers
        superusers = User.objects.filter(is_superuser=True).exclude(id=self.request.user.id)
        for superuser in superusers:
            superuser.customers.add(self.object)
        
        messages.success(self.request,
                         mark_safe(f"Account <strong>{self.object.customer_name}</strong> has been created"))
        return response

class CustomerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    permission_required = 'customers.change_customer'

    def get_success_url(self):
        return reverse('customers:customer-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request,
                      mark_safe(f"Account <strong>{self.object.customer_name}</strong> has been updated."),
                      extra_tags='alert-primary')
        return response

class CustomerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    permission_required = 'customers.delete_customer'

    def get_success_url(self):
        return reverse('customers:customer-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        customer_name = self.object.customer_name
        self.object.delete()
        messages.warning(self.request,
                         mark_safe(f"Account <strong>{customer_name}</strong> has been deleted."),
                         extra_tags='alert-warning')
        return HttpResponseRedirect(success_url)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)