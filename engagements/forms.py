from django import forms
from .models import Engagement, TimeEntry

class EngagementForm(forms.ModelForm):
    class Meta:
        model = Engagement
        fields = [
            'name', 'priority', 'contract_service',
            'client_description', 'internal_notes'
        ]
        widgets = {
            'contract_service': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, contract_services=None, **kwargs):
        super().__init__(*args, **kwargs)
        if contract_services:
            self.fields['contract_service'].queryset = contract_services
            # Customize the display of contract services
            self.fields['contract_service'].label_from_instance = lambda obj: f"{obj.contract.contract_id} - {obj.service.service_name} (Qty: {obj.quantity})"

    def clean(self):
        cleaned_data = super().clean()
        if hasattr(self, 'instance') and 'contract_service' in cleaned_data:
            contract_service = cleaned_data['contract_service']
            self.instance.contract = contract_service.contract
            self.instance.customer = contract_service.contract.customer
        return cleaned_data
    
class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['client_comment', 'internal_notes', 'hours_spent']
        widgets = {
            'client_comment': forms.Textarea(attrs={'class': 'form-control'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control'}),
            'hours_spent': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0.5'
            }),
        }

    def __init__(self, *args, engagement=None, **kwargs):
        self.engagement = engagement
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if hasattr(self, 'instance'):
            self.instance.engagement = self.engagement
        return cleaned_data