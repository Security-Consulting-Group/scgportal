from django.db.models import Q
from .base import SignatureListView, SignatureDetailView, SignatureCreateView, SignatureUpdateView, SignatureDeleteView
from signatures.models import BurpSuiteSignature
from signatures.forms import BurpSuiteSignatureForm

class BurpSuiteSignatureListView(SignatureListView):
    model = BurpSuiteSignature
    permission_required = 'signatures.view_burpsuitesignature'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        signature_id = self.request.GET.get('id')
        search_query = self.request.GET.get('search')

        if signature_id:
            queryset = queryset.filter(id=signature_id)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        return queryset

class BurpSuiteSignatureDetailView(SignatureDetailView):
    model = BurpSuiteSignature
    permission_required = 'signatures.view_burpsuitesignature'

class BurpSuiteSignatureCreateView(SignatureCreateView):
    model = BurpSuiteSignature
    form_class = BurpSuiteSignatureForm
    permission_required = 'signatures.add_burpsuitesignature'

class BurpSuiteSignatureUpdateView(SignatureUpdateView):
    model = BurpSuiteSignature
    form_class = BurpSuiteSignatureForm
    permission_required = 'signatures.change_burpsuitesignature'

class BurpSuiteSignatureDeleteView(SignatureDeleteView):
    model = BurpSuiteSignature
    permission_required = 'signatures.delete_burpsuitesignature'