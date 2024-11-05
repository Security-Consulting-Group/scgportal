# engagements/views/time_entries.py
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from ..models import TimeEntry, Engagement
from customers.models import Customer
from django.utils import timezone
from ..forms import TimeEntryForm



class TimeEntryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'engagements/time_entry_form.html'
    permission_required = 'engagements.add_timeentry'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['engagement'] = self.get_engagement()
        return kwargs

    def get_engagement(self):
        return get_object_or_404(
            Engagement,
            engagement_id=self.kwargs['engagement_id'],
            customer__customer_id=self.kwargs['customer_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['engagement'] = self.get_engagement()
        context['customer'] = context['engagement'].customer
        context['selected_customer'] = context['customer']
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.date = timezone.now().date()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engagements:engagement-detail', kwargs={
            'customer_id': self.kwargs['customer_id'],
            'engagement_id': self.kwargs['engagement_id']
        })

class TimeEntryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TimeEntry
    fields = ['client_comment', 'internal_notes', 'hours_spent', 'date']
    template_name = 'engagements/time_entry_form.html'
    permission_required = 'engagements.change_timeentry'

    def get_success_url(self):
        return reverse_lazy('engagements:detail', kwargs={
            'customer_id': self.kwargs['customer_id'],
            'pk': self.kwargs['engagement_pk']
        })