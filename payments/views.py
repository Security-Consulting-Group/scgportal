from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.mixins import SelectedCustomerRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from .models import Payment
from .forms import PaymentForm
from contracts.models import Contract
from customers.models import Customer

class PaymentCreateView(SelectedCustomerRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    permission_required = 'payments.add_payment'

    def form_valid(self, form):
        contract = get_object_or_404(Contract, contract_id=self.kwargs['contract_id'])
        customer = get_object_or_404(Customer, customer_id=self.kwargs['customer_id'])
        
        if contract.customer != customer:
            return JsonResponse({'success': False, 'message': 'Invalid contract for this customer.'}, status=403)
        
        if customer not in self.request.user.customers.all() and not self.request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'You do not have permission to add payments to this contract.'}, status=403)
        
        form.instance.contract = contract
        self.object = form.save()
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Payment added successfully.'
            })
        
        messages.success(self.request, 'Payment added successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('contracts:contract-detail', kwargs={
            'customer_id': self.kwargs['customer_id'],
            'contract_id': self.object.contract.contract_id
        })

class PaymentListView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    permission_required = 'payments.view_payment'

    def get_queryset(self):
        contract = get_object_or_404(Contract, id=self.kwargs['contract_id'], customer=self.get_selected_customer())
        return Payment.objects.filter(contract=contract)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract'] = get_object_or_404(Contract, id=self.kwargs['contract_id'], customer=self.get_selected_customer())
        return context

from django.core.exceptions import PermissionDenied

class PaymentDetailView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'
    permission_required = 'payments.view_payment'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.contract.customer != self.get_selected_customer():
            raise PermissionDenied("You do not have permission to view this payment.")
        return obj