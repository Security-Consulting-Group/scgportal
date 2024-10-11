from django import forms
import json
from customers.models import Customer
from contracts.models import Contract
from services.models import Service

class ReportUploadForm(forms.Form):
    json_file = forms.FileField(label='JSON File')
    contract = forms.ModelChoiceField(queryset=Contract.objects.none(), required=False)
    report_type = forms.ModelChoiceField(queryset=Service.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        self.customer = kwargs.pop('customer', None)
        super().__init__(*args, **kwargs)
        if self.customer:
            self.fields['contract'].queryset = Contract.objects.filter(customer=self.customer)

        # If contract is selected, filter services for that contract
        if self.data.get('contract'):
            try:
                contract_id = self.data.get('contract')
                self.fields['report_type'].queryset = Service.objects.filter(
                    contractservice__contract__contract_id=contract_id
                ).distinct()
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset

    def clean(self):
        cleaned_data = super().clean()
        contract = cleaned_data.get('contract')
        report_type = cleaned_data.get('report_type')

        if contract and report_type:
            # Verify that the selected report_type is valid for the selected contract
            valid_services = Service.objects.filter(contractservice__contract=contract)
            if report_type not in valid_services:
                self.add_error('report_type', 'Invalid report type for the selected contract.')

        return cleaned_data

    def clean_json_file(self):
        json_file = self.cleaned_data['json_file']
        try:
            data = json.load(json_file)
            required_keys = ['scan_date', 'inventory', 'alert_report']
            for key in required_keys:
                if key not in data:
                    raise forms.ValidationError(f"The JSON file is missing the '{key}' key.")
            json_file.seek(0)  # Reset file pointer
            return json_file
        except json.JSONDecodeError:
            raise forms.ValidationError("The uploaded file is not a valid JSON file.")
        
    def get_services_for_contract(self, contract_id):
        if contract_id:
            contract = Contract.objects.get(contract_id=contract_id)
            return Service.objects.filter(contractservice__contract=contract).distinct()
        return Service.objects.none()