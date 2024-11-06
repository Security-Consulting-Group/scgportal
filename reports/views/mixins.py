from django.db import models
from django.http import JsonResponse

class StatusSummaryMixin:
    def get_status_summary(self):
        if hasattr(self, 'object') and hasattr(self.object, 'vulnerabilities'):
            # Get STATUS_CHOICES from the model
            model = self.object.vulnerabilities.model
            status_choices = dict(model.STATUS_CHOICES)
            
            # Get counts from database
            counts = (
                self.object.vulnerabilities
                .values('status')
                .annotate(count=models.Count('id'))
                .order_by('status')
            )
            
            # Convert to dictionary with proper labels
            return {
                status['status']: {
                    'label': status_choices[status['status']],
                    'count': status['count']
                }
                for status in counts
                if status['count'] > 0  # Only include non-zero counts
            }
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_summary'] = self.get_status_summary()
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('counts_only'):
            return JsonResponse({'status_summary': self.get_status_summary()})
            
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)