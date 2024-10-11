from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import PermissionRequiredMixin
from core.mixins import SelectedCustomerRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.forms import inlineformset_factory
from contracts.models import Contract, ContractService
from contracts.forms import ContractForm, ServiceQuantityForm
from customers.models import Customer
from payments.forms import PaymentForm
from django.contrib import messages
from decimal import Decimal
from django.utils import timezone

ServiceFormSet = inlineformset_factory(
    Contract, 
    ContractService, 
    form=ServiceQuantityForm, 
    extra=1,
    can_delete=True,
    fields=['service', 'quantity', 'discount']
)

class ContractListView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, ListView):
    model = Contract
    template_name = 'contracts/contract_list.html'
    context_object_name = 'contracts'
    permission_required = 'contracts.view_contract'

    def get_queryset(self):
        return Contract.objects.filter(customer=self.request.selected_customer)

class ContractDetailView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Contract
    template_name = 'contracts/contract_detail.html'
    context_object_name = 'contract'
    permission_required = 'contracts.view_contract'
    pk_url_kwarg = 'contract_id'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            contract_id=self.kwargs['contract_id'],
            customer=self.request.selected_customer
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payments'] = self.object.payments.all().order_by('-payment_date')
        context['payment_form'] = PaymentForm()
        
        contract_services = self.object.contractservice_set.all()
        for cs in contract_services:
            cs.subtotal = cs.service.service_price * cs.quantity
            if cs.discount:
                discount_amount = cs.subtotal * (cs.discount / Decimal('100'))
            else:
                discount_amount = cs.subtotal * (self.object.discount / Decimal('100')) if self.object.discount else Decimal('0')
            cs.discounted_subtotal = cs.subtotal - discount_amount
            cs.total = cs.discounted_subtotal * (1 + self.object.taxes / Decimal('100'))
        
        context['contract_services'] = contract_services
        return context

class ContractCreateView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'
    permission_required = 'contracts.add_contract'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_update'] = False
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.customer = self.get_selected_customer()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.request.selected_customer
        if self.request.POST:
            context['services'] = ServiceFormSet(self.request.POST, instance=self.object)
        else:
            context['services'] = ServiceFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        services = context['services']
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.customer = self.request.selected_customer
            
            # Generate contract_id
            now = timezone.now()
            self.object.contract_id = now.strftime("C-%Y%m%d-%H%M%S")
            
            self.object.save()
            if services.is_valid():
                services.instance = self.object
                services.save()
            else:
                return self.form_invalid(form)
            self.object.calculate_total()
        messages.success(self.request, 'Contract created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('contracts:contract-list', kwargs={'customer_id': self.request.selected_customer.customer_id})

class ContractUpdateView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'
    permission_required = 'contracts.change_contract'
    pk_url_kwarg = 'contract_id'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_update'] = True
        return kwargs

    def get_success_url(self):
        return reverse_lazy('contracts:contract-detail', kwargs={
            'customer_id': self.get_selected_customer().customer_id,
            'contract_id': self.object.contract_id
        })
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.get_selected_customer()
        if self.request.POST:
            context['services'] = ServiceFormSet(self.request.POST, instance=self.object)
        else:
            context['services'] = ServiceFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        services = context['services']
        with transaction.atomic():
            self.object = form.save(commit=False)
            if services.is_valid():
                services.instance = self.object
                self.object.save()
                services.save()
            else:
                return self.form_invalid(form)
            self.object.calculate_total()
        messages.success(self.request, 'Contract updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        services = context['services']
        return self.render_to_response(self.get_context_data(form=form))

class ContractDeleteView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Contract
    template_name = 'contracts/contract_confirm_delete.html'
    permission_required = 'contracts.delete_contract'
    context_object_name = 'contract'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            contract_id=self.kwargs['contract_id'],
            customer__customer_id=self.kwargs['customer_id']
        )

    def get_success_url(self):
        return reverse_lazy('contracts:contract-list', kwargs={'customer_id': self.object.customer.customer_id})