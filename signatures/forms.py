from django import forms
from .models import Signature

class SignatureForm(forms.ModelForm):
    class Meta:
        model = Signature
        fields = ['id', 'plugin_name', 'description']
        widgets = {
            'id': forms.NumberInput(attrs={'class': 'form-control'}),
            'plugin_name': forms.TextInput(attrs={'class': 'form-control'}),
            'risk_factor': forms.Select(choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical')], attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        }

    def clean_id(self):
        plugin_id = self.cleaned_data.get('id')
        if plugin_id <= 0:
            raise forms.ValidationError("Plugin ID must be a positive integer.")
        return plugin_id

class SignatureUploadForm(forms.Form):
    json_file = forms.FileField(
        label='Select a JSON file',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    scanner_type = forms.ChoiceField(
        choices=Signature.SCANNER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )