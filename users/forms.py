from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from customers.models import Customer
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import CustomGroup, CustomUser


class CustomLoginForm(AuthenticationForm):
    customer_name = forms.CharField(max_length=100, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'

User = get_user_model()

class CustomLoginForm(AuthenticationForm):
    customer_name = forms.CharField(max_length=100, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'

class CustomUserFormMixin:
    """Mixin for shared user form functionality"""
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        if self.current_user:
            self._setup_field_querysets()
            self._handle_non_staff_fields()

    def _setup_field_querysets(self):
        """Setup querysets for customers and groups fields"""
        if 'customers' in self.fields:
            self.fields['customers'].queryset = (
                Customer.objects.all() if self.current_user.is_staff 
                else self.current_user.customers.all()
            )

        if 'groups' in self.fields:
            user_type = (
                self.current_user.type if self.current_user.is_staff
                else self.instance.type if self.instance and self.instance.pk
                else CustomUser.UserType.NORMAL
            )
            self.fields['groups'].queryset = CustomGroup.get_visible_groups(user_type)

    def _handle_non_staff_fields(self):
        """Remove fields that non-staff users shouldn't see"""
        if not self.current_user.is_staff:
            if 'type' in self.fields:
                del self.fields['type']
            if hasattr(self, 'instance') and not self.instance.pk and 'is_active' in self.fields:
                del self.fields['is_active']

    def clean(self):
        """Consolidated validation logic"""
        cleaned_data = super().clean()
        user_type = (
            cleaned_data.get('type') or 
            getattr(self.instance, 'type', CustomUser.UserType.NORMAL)
        )
        customers = cleaned_data.get('customers')
        groups = cleaned_data.get('groups')

        self._validate_customer_count(user_type, customers)
        self._validate_group_visibility(user_type, groups)

        return cleaned_data

    def _validate_customer_count(self, user_type, customers):
        """Validate customer count based on user type"""
        if (user_type == CustomUser.UserType.NORMAL and 
            customers and len(customers) > 1):
            raise forms.ValidationError(
                "Normal users can only be assigned to one customer."
            )

    def _validate_group_visibility(self, user_type, groups):
        """Validate group visibility based on user type"""
        if groups:
            visible_groups = CustomGroup.get_visible_groups(user_type)
            invalid_groups = groups.exclude(
                id__in=visible_groups.values_list('id', flat=True)
            )
            if invalid_groups.exists():
                raise forms.ValidationError(
                    f"The following groups are not available for this user type: "
                    f"{', '.join(invalid_groups.values_list('name', flat=True))}"
                )

class CustomUserCreationForm(CustomUserFormMixin, forms.ModelForm):
    customers = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=CustomGroup.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    type = forms.ChoiceField(
        choices=CustomUser.UserType.choices,
        initial=CustomUser.UserType.NORMAL,
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'customers', 'groups', 'type')

    def save(self, commit=True):
        user = super().save(commit=False)
        if 'type' in self.cleaned_data:
            user.type = self.cleaned_data['type']
        if commit:
            user.save()
            if 'customers' in self.cleaned_data:
                user.customers.set(self.cleaned_data['customers'])
            self.save_m2m()
        return user

class CustomUserChangeForm(CustomUserFormMixin, forms.ModelForm):
    customers = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=CustomGroup.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    type = forms.ChoiceField(
        choices=CustomUser.UserType.choices,
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'customers', 
                 'groups', 'is_active', 'type')

    def clean_email(self):
        email = self.cleaned_data["email"]
        if CustomUser.objects.filter(email=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email
    
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