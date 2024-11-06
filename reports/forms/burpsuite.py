from django import forms
import json
from contracts.models import Contract

class BurpSuiteReportUploadForm(forms.Form):
    name = forms.CharField(max_length=255, label='Report Name')
    json_file = forms.FileField(label='JSON File')
    contract = forms.ModelChoiceField(queryset=Contract.objects.none(), required=True)

    def __init__(self, *args, **kwargs):
        customer = kwargs.pop('customer', None)
        service = kwargs.pop('service', None)
        super().__init__(*args, **kwargs)
        if customer:
            # Filter by customer and status
            self.fields['contract'].queryset = Contract.objects.filter(
                customer=customer,
                contract_status__in=['TRIAL', 'ACTIVE']
            )
        
        if service:
            # Further filter by service while maintaining status filter
            self.fields['contract'].queryset = self.fields['contract'].queryset.filter(
                contractservice__service=service
            ).distinct()

    def clean_json_file(self):
        json_file = self.cleaned_data['json_file']
        try:
            data = json.load(json_file)
            required_keys = ['exportTime', 'issues']
            for key in required_keys:
                if key not in data:
                    raise forms.ValidationError(f"The JSON file is missing the '{key}' key.")
            json_file.seek(0)  # Reset file pointer
            return json_file
        except json.JSONDecodeError:
            raise forms.ValidationError("The uploaded file is not a valid JSON file.")