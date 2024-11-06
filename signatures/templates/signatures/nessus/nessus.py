from django.db.models import Q
from .base import SignatureListView, SignatureDetailView, SignatureCreateView, SignatureUpdateView, SignatureDeleteView
from signatures.models import NessusSignature
from signatures.forms import NessusSignatureForm

class NessusSignatureListView(SignatureListView):
    model = NessusSignature
    permission_required = 'signatures.view_nessussignature'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        severity = self.request.GET.get('severity')
        signature_id = self.request.GET.get('id')
        search_query = self.request.GET.get('search')

        if severity:
            queryset = queryset.filter(risk_factor=severity)
        if signature_id:
            queryset = queryset.filter(id=signature_id)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['severity_choices'] = NessusSignature.RISK_FACTOR_CHOICES
        return context

class NessusSignatureDetailView(SignatureDetailView):
    model = NessusSignature
    permission_required = 'signatures.view_nessussignature'

class NessusSignatureCreateView(SignatureCreateView):
    model = NessusSignature
    form_class = NessusSignatureForm
    permission_required = 'signatures.add_nessussignature'

class NessusSignatureUpdateView(SignatureUpdateView):
    model = NessusSignature
    form_class = NessusSignatureForm
    permission_required = 'signatures.change_nessussignature'

class NessusSignatureDeleteView(SignatureDeleteView):
    model = NessusSignature
    permission_required = 'signatures.delete_nessussignature'