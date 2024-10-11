# import uuid
# from django import forms
# from .models import Customer

# class CustomerForm(forms.ModelForm):
#     class Meta:
#         model = Customer
#         fields = ['customer_name']  # Exclude customer_id from the form

#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         if not instance.pk:  # If it's a new instance
#             instance.customer_id = uuid.uuid4()  # Generate a new UUID
#         if commit:
#             instance.save()
#         return instance
from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_name']