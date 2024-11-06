from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.urls import reverse_lazy
from ..models import Engagement
from ..forms import EngagementForm
from customers.models import Customer
from contracts.models import Contract, ContractService
from django.contrib import messages

class EngagementListView(LoginRequiredMixin, ListView):
    model = Engagement
    template_name = 'engagements/engagement_list.html'
    context_object_name = 'engagements'

    def get_queryset(self):
        self.customer = get_object_or_404(
            Customer, 
            customer_id=self.kwargs['customer_id']
        )
        queryset = Engagement.objects.filter(
            customer=self.customer
        ).select_related(
            'contract',
            'contract_service',
            'created_by'
        )

        # Contract filter
        contract_id = self.request.GET.get('contract')
        if contract_id:
            queryset = queryset.filter(contract__contract_id=contract_id)

        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by priority if provided
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.customer
        context['selected_customer'] = self.customer
        context['selected_status'] = self.request.GET.get('status')
        context['selected_priority'] = self.request.GET.get('priority')
        context['contracts'] = Contract.objects.filter(
            customer=self.customer,
            engagement__isnull=False
        ).distinct()
        context['selected_contract'] = self.request.GET.get('contract')
        # Check for active contracts with support services
        has_valid_contracts = Contract.objects.filter(
            customer=self.customer,
            contract_status__in=['ACTIVE', 'TRIAL'],
            contractservice__service__report_type__name__iexact='support'
        ).exists()
        
        context['has_valid_contracts'] = has_valid_contracts
        return context
    
class EngagementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
   model = Engagement
   form_class = EngagementForm
   template_name = 'engagements/engagement_form.html'
   permission_required = 'engagements.add_engagement'

   def dispatch(self, request, *args, **kwargs):
       self.customer = get_object_or_404(
           Customer, 
           customer_id=self.kwargs['customer_id']
       )

       # Get ALL active/trial contracts with support services
       self.contracts = Contract.objects.filter(
           customer=self.customer,
           contract_status__in=['ACTIVE', 'TRIAL']
       )
       
       if not self.contracts.exists():
           raise Http404("No active contracts found for this customer")

       # Get all contract services for support
       self.contract_services = ContractService.objects.filter(
           contract__in=self.contracts,
           service__report_type__name__iexact='support'
       ).select_related('contract', 'service')
           
       return super().dispatch(request, *args, **kwargs)

   def get_form_kwargs(self):
       kwargs = super().get_form_kwargs()
       # Pass contract services instead of single contract
       kwargs['contract_services'] = self.contract_services
       return kwargs

   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['customer'] = self.customer
       context['selected_customer'] = self.customer
       return context

   def get_success_url(self):
       return reverse_lazy('engagements:engagement-detail', kwargs={
           'customer_id': self.kwargs['customer_id'],
           'engagement_id': self.object.engagement_id
       })

   def form_valid(self, form):
       form.instance.created_by = self.request.user
       return super().form_valid(form)
        
class EngagementDetailView(LoginRequiredMixin, DetailView):
    model = Engagement
    template_name = 'engagements/engagement_detail.html'
    context_object_name = 'engagement'
    pk_url_kwarg = 'engagement_id'  # Add this line

    def get_queryset(self):
        self.customer = get_object_or_404(
            Customer, 
            customer_id=self.kwargs['customer_id']
        )
        return Engagement.objects.filter(customer=self.customer)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.customer
        context['selected_customer'] = self.customer
        context['time_entries'] = self.object.timeentry_set.all().order_by('-date')
        return context

class EngagementUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Engagement
    form_class = EngagementForm
    template_name = 'engagements/engagement_form.html'
    permission_required = 'engagements.change_engagement'
    pk_url_kwarg = 'engagement_id'

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(
            Customer, 
            customer_id=self.kwargs['customer_id']
        )

        # Get ALL active/trial contracts with support services
        self.contracts = Contract.objects.filter(
            customer=self.customer,
            contract_status__in=['ACTIVE', 'TRIAL']
        )
        
        # Get all contract services for support
        self.contract_services = ContractService.objects.filter(
            contract__in=self.contracts,
            service__report_type__name__iexact='support'
        ).select_related('contract', 'service')
            
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['contract_services'] = self.contract_services
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.customer
        context['selected_customer'] = self.customer
        return context

    def get_success_url(self):
        return reverse_lazy('engagements:engagement-detail', kwargs={
            'customer_id': self.kwargs['customer_id'],
            'engagement_id': self.object.engagement_id
        })

class EngagementDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Engagement
    template_name = 'engagements/engagement_confirm_delete.html'
    permission_required = 'engagements.delete_engagement'
    pk_url_kwarg = 'engagement_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.object.customer
        context['selected_customer'] = self.object.customer
        return context

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Engagement {self.object.engagement_id} was successfully deleted.")
        return response

    def get_success_url(self):
        return reverse_lazy('engagements:engagement-list', kwargs={
            'customer_id': self.kwargs['customer_id']
        })
        
class EngagementStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Engagement
    fields = ['status']
    permission_required = 'engagements.change_engagement'
    template_name = 'engagements/engagement_status_form.html'
    pk_url_kwarg = 'engagement_id'  # Add this line

    def get_queryset(self):
        return Engagement.objects.filter(
            customer__customer_id=self.kwargs['customer_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.object.customer
        context['selected_customer'] = context['customer']
        return context

    def get_success_url(self):
        return reverse_lazy('engagements:engagement-detail', kwargs={
            'customer_id': self.kwargs['customer_id'],
            'engagement_id': self.object.engagement_id  # Update this
        })