from django import forms
from .models import NessusSignature, BurpSuiteSignature

class NessusSignatureForm(forms.ModelForm):
    class Meta:
        model = NessusSignature
        fields = ['id', 'name', 'description', 'risk_factor', 'solution', 'cvss_base_score']
        widgets = {
            'id': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'risk_factor': forms.Select(attrs={'class': 'form-control'}),
            'solution': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'cvss_base_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_id(self):
        plugin_id = self.cleaned_data.get('id')
        if plugin_id <= 0:
            raise forms.ValidationError("Signature ID must be a positive integer.")
        return plugin_id

class BurpSuiteSignatureForm(forms.ModelForm):
    class Meta:
        model = BurpSuiteSignature
        fields = ['id', 'name', 'description', 'remediation', 'vulnerability_classifications', 'retired']
        widgets = {
            'id': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'remediation': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'vulnerability_classifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'retired': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_id(self):
        signature_id = self.cleaned_data.get('id')
        if signature_id <= 0:
            raise forms.ValidationError("Signature ID must be a positive integer.")
        return signature_id

class SignatureUploadForm(forms.Form):
    json_file = forms.FileField(
        label='Select a JSON file',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    scanner_type = forms.ChoiceField(
        choices=[('Nessus', 'Nessus'), ('BurpSuite', 'Burp Suite')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )