from django import forms
from .models import Service, ReportType

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['service_id', 'service_name', 'service_description', 'service_price', 'is_active', 'report_type']
        widgets = {
            'is_active': forms.CheckboxInput(),
            'service_description': forms.Textarea(attrs={'rows': 5}),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['report_type'].queryset = ReportType.objects.filter(is_active=True)
        self.fields['report_type'].empty_label = "Select a report type"

class ReportTypeForm(forms.ModelForm):
    class Meta:
        model = ReportType
        fields = ['name', 'description', 'is_active']