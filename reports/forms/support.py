from django import forms
from ..models import Support
from contracts.models import Contract

class SupportForm(forms.ModelForm):
    class Meta:
        model = Support
        fields = ['name', 'contract', 'comments', 'loe']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        customer = kwargs.pop('customer', None)
        service = kwargs.pop('service', None)
        super().__init__(*args, **kwargs)
        
        if customer:
            self.fields['contract'].queryset = Contract.objects.filter(customer=customer)
        
        if service:
            self.fields['contract'].queryset = self.fields['contract'].queryset.filter(
                contractservice__service=service
            ).distinct()