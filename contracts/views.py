from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from core.mixins import SelectedCustomerRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from contracts.models import Contract, ContractService
from contracts.forms import ContractForm, ServiceQuantityForm
from payments.forms import PaymentForm
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError


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
        # Update expired contracts first
        Contract.objects.filter(
            contract_end_date__lt=timezone.now().date(),
            contract_status__in=['ACTIVE', 'TRIAL', 'NOTSTARTED']
        ).update(contract_status='EXPIRED')

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
        messages.success(self.request,
                         mark_safe(f"Contract '<strong>{self.object.contract_id}</strong>' has been created successfully."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('contracts:contract-list', kwargs={'customer_id': self.request.selected_customer.customer_id})


import logging

logger = logging.getLogger(__name__)

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
        try:
            with transaction.atomic():
                self.object = form.save(commit=False)
                if services.is_valid():
                    logger.info(f"Services formset is valid for contract {self.object.contract_id}")
                    services.instance = self.object
                    self.object.save()
                    services.save()
                    logger.info(f"Contract {self.object.contract_id} and its services saved successfully")
                else:
                    logger.error(f"Services formset is invalid for contract {self.object.contract_id}: {services.errors}")
                    return self.form_invalid(form)
                self.object.calculate_total()
            messages.info(self.request,
                          mark_safe(f"Contract '<strong>{self.object.contract_id}</strong>' has been updated successfully."),
                          extra_tags='alert-primary')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            form.add_error(None, "An unexpected error occurred. Please try again.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.error(f"Form is invalid for contract {self.object.contract_id if self.object else 'New'}: {form.errors}")
        context = self.get_context_data()
        services = context['services']
        if not services.is_valid():
            logger.error(f"Services formset is invalid: {services.errors}")
        for field, errors in form.errors.items():
            logger.error(f"Field '{field}' errors: {errors}")
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

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        contract_id = self.object.contract_id
        self.object.delete()
        messages.warning(self.request,
                         mark_safe(f"Contract '<strong>{contract_id}</strong>' has been deleted successfully."),
                         extra_tags='alert-warning')
        return HttpResponseRedirect(success_url)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
    
class ContractStatusChangeView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'contracts.change_contract'

    def post(self, request, *args, **kwargs):
        contract = get_object_or_404(Contract, 
                                     contract_id=kwargs['contract_id'], 
                                     customer=self.request.selected_customer)
        new_status = request.POST.get('status')
        if new_status in dict(Contract.CONTRACT_STATUS_CHOICES):
            contract.contract_status = new_status
            contract.save()
            return JsonResponse({
                'success': True,
                'new_status': contract.get_contract_status_display()
            })
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    
class ContractServiceDeleteView(View):
    def post(self, request, *args, **kwargs):
        try:
            contract_service = get_object_or_404(
                ContractService, 
                id=kwargs['service_id'], 
                contract__contract_id=kwargs['contract_id'], 
                contract__customer__customer_id=kwargs['customer_id']
            )
            
            if not request.user.has_perm('contracts.delete_contractservice'):
                raise PermissionDenied

            service_name = contract_service.service.service_name
            contract = contract_service.contract
            contract_service.delete()

            contract.calculate_total()

            messages.warning(request,
                             mark_safe(f"Service '<strong>{service_name}</strong>' has been successfully removed from the contract."),
                             extra_tags='alert-warning')
            
            return JsonResponse({
                'success': True, 
                'message': f"Service '{service_name}' has been successfully removed from the contract.",
                'contract_data': {
                    'sub_total': str(contract.sub_total),
                    'discount': str(contract.discount) if contract.discount is not None else 'N/A',
                    'taxes': str(contract.taxes),
                    'taxes_amount': str(contract.taxes_amount),
                    'total': str(contract.total),
                    'balance': str(contract.balance)
                }
            })
        except PermissionDenied:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)