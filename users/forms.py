from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from customers.models import Customer
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm


class CustomLoginForm(AuthenticationForm):
    customer_name = forms.CharField(max_length=100, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'

User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):
    customers = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    type = forms.ChoiceField(choices=User.UserType.choices, initial=User.UserType.NORMAL, required=False)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'customers', 'groups', 'type')

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if self.current_user:
            if self.current_user.is_staff:
                self.fields['customers'].queryset = Customer.objects.all()
            else:
                self.fields['customers'].queryset = self.current_user.customers.all()
                del self.fields['type']  # Remove type field for non-staff users

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('type') or User.UserType.NORMAL
        customers = cleaned_data.get('customers')

        if user_type == User.UserType.NORMAL and customers and len(customers) > 1:
            raise forms.ValidationError("Normal users can only be assigned to one customer.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(User.objects.make_random_password())
        if 'type' in self.cleaned_data:
            user.type = self.cleaned_data['type']
        if commit:
            user.save()
            self.save_m2m()
        return user

class CustomUserChangeForm(forms.ModelForm):
    customers = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    type = forms.ChoiceField(choices=User.UserType.choices, required=False)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'customers', 'groups', 'is_active', 'type')

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if self.current_user:
            if self.current_user.is_staff:
                self.fields['customers'].queryset = Customer.objects.all()
            else:
                self.fields['customers'].queryset = self.current_user.customers.all()
                del self.fields['is_active']
                del self.fields['type']  # Remove type field for non-staff users

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('type') or self.instance.type
        customers = cleaned_data.get('customers')

        if user_type == User.UserType.NORMAL and customers and len(customers) > 1:
            raise forms.ValidationError("Normal users can only be assigned to one customer.")

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        if 'type' in self.cleaned_data:
            user.type = self.cleaned_data['type']
        if commit:
            user.save()
            self.save_m2m()
        return user
    
class ProfileUpdateForm(forms.ModelForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave this blank if you don't want to change your password."
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 or new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("The two password fields didn't match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password1')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user