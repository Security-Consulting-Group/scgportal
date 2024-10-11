from django import forms
from .models import Service

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['service_id', 'service_name', 'service_description', 'service_price', 'is_active']
        widgets = {
            'is_active': forms.CheckboxInput(),
            'service_description': forms.Textarea(attrs={'rows': 3}),
        }