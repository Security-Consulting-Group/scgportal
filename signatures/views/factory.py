from django.http import Http404
from django.views.generic import TemplateView
from .nessus import (
    NessusSignatureListView, NessusSignatureDetailView, NessusSignatureCreateView,
    NessusSignatureUpdateView, NessusSignatureDeleteView
)
from .burpsuite import (
    BurpSuiteSignatureListView, BurpSuiteSignatureDetailView, BurpSuiteSignatureCreateView,
    BurpSuiteSignatureUpdateView, BurpSuiteSignatureDeleteView
)

class SignatureViewFactory:
    VIEWS = {
        'nessus': {
            'list': NessusSignatureListView,
            'detail': NessusSignatureDetailView,
            'create': NessusSignatureCreateView,
            'update': NessusSignatureUpdateView,
            'delete': NessusSignatureDeleteView,
        },
        'burpsuite': {
            'list': BurpSuiteSignatureListView,
            'detail': BurpSuiteSignatureDetailView,
            'create': BurpSuiteSignatureCreateView,
            'update': BurpSuiteSignatureUpdateView,
            'delete': BurpSuiteSignatureDeleteView,
        },
    }

    @classmethod
    def get_view(cls, scanner_type, view_type):
        try:
            return cls.VIEWS[scanner_type.lower()][view_type]
        except KeyError:
            raise Http404(f"Unsupported scanner type or view type: {scanner_type} - {view_type}")

def signature_selection_view(request):
    return TemplateView.as_view(template_name='signatures/signature_selection.html')(request)

def signature_list_view(request, scanner_type):
    view_class = SignatureViewFactory.get_view(scanner_type, 'list')
    return view_class.as_view()(request, scanner_type=scanner_type)

def signature_detail_view(request, scanner_type, pk):
    view_class = SignatureViewFactory.get_view(scanner_type, 'detail')
    return view_class.as_view()(request, scanner_type=scanner_type, pk=pk)

def signature_create_view(request, scanner_type):
    view_class = SignatureViewFactory.get_view(scanner_type, 'create')
    return view_class.as_view()(request, scanner_type=scanner_type)

def signature_update_view(request, scanner_type, pk):
    view_class = SignatureViewFactory.get_view(scanner_type, 'update')
    return view_class.as_view()(request, scanner_type=scanner_type, pk=pk)

def signature_delete_view(request, scanner_type, pk):
    view_class = SignatureViewFactory.get_view(scanner_type, 'delete')
    return view_class.as_view()(request, scanner_type=scanner_type, pk=pk)