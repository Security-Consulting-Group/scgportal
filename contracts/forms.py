from django import forms
from .models import Contract, ContractService, Service

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        exclude = ['customer', 'contract_id']
        fields = ['contract_start_date', 'contract_end_date', 'contract_status', 'discount', 'taxes', 'contract_notes']
        widgets = {
            'contract_start_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        is_update = kwargs.pop('is_update', False)
        super().__init__(*args, **kwargs)
        
        if not is_update:
            del self.fields['contract_status']

class ServiceQuantityForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=1, initial=1)
    discount = forms.DecimalField(max_digits=5, decimal_places=2, required=False, min_value=0, max_value=100)

    class Meta:
        model = ContractService
        fields = ['service', 'quantity', 'discount']

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None or quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is not None and (discount < 0 or discount > 100):
            raise forms.ValidationError("Discount must be between 0 and 100.")
        return discount