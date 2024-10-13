from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.mixins import SelectedCustomerRequiredMixin
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomLoginForm, ProfileUpdateForm
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.core.exceptions import ValidationError
from django.contrib.auth import login as auth_login
from django.http import HttpResponseRedirect


User = get_user_model()

class CustomLoginView(LoginView):
    template_name = 'users/login.html'

    def form_invalid(self, form):
        messages.error(self.request, "Invalid credentials. Please try again.")
        return super().form_invalid(form)

    def form_valid(self, form):
        user = form.get_user()
        
        try:
            # Check if the user is a normal user with multiple customers
            if user.type == user.UserType.NORMAL and user.customers.count() > 1:
                raise ValidationError("Normal users can only be assigned to one customer. Please contact an administrator.")
            
            # Perform the login
            auth_login(self.request, user)
            
            # Set the default customer for normal users
            if user.type == user.UserType.NORMAL:
                default_customer = user.get_default_customer()
                if default_customer:
                    self.request.session['selected_customer_id'] = str(default_customer.customer_id)
            
            return redirect(self.get_success_url())
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('root')  # This will use the DashboardRedirectView logic

class UserListView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    permission_required = ('users.view_customuser', 'users.view_customer_user')

    def get_queryset(self):
        queryset = User.objects.filter(customers=self.selected_customer)
        
        # Only show staff users if the customer type is "main"
        if self.selected_customer.customer_type != 'main':
            queryset = queryset.filter(is_staff=False)
        
        return queryset

    def has_permission(self):
        return super().has_permission() and self.selected_customer in self.request.user.customers.all()

class UserCreateView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    permission_required = ('users.add_customuser', 'users.add_customer_user')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            user = form.save(commit=False)
            user.save()
            customers = form.cleaned_data.get('customers')
            if customers:
                user.customers.set(customers)
            form.save_m2m()  # Save many-to-many relationships
            messages.success(self.request, f"User {user.email} has been created.")
            return redirect(self.get_success_url())
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "This type of user can only be assigned to one customer. Please reach out to support to fix this issue.", extra_tags='danger')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('users:user-list', kwargs={'customer_id': self.selected_customer.customer_id})

    def has_permission(self):
        return super().has_permission() and any(self.request.user.has_perm(perm) for perm in self.permission_required)

class UserUpdateView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    permission_required = ('users.change_customuser', 'users.change_customer_user')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f"User {self.object.email} has been updated.")
            return response
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "This type of user can only be assigned to one customer. Please reach out to support to fix this issue.", extra_tags='danger')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('users:user-list', kwargs={'customer_id': self.selected_customer.customer_id})

    def has_permission(self):
        return super().has_permission() and self.get_object().customers.filter(customer_id=self.selected_customer.customer_id).exists()

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'users/profile_update.html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.save()
        # messages.success(self.request, 'Your profile has been updated successfully.')
        return HttpResponseRedirect(self.request.path_info)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['messages'] = messages.get_messages(self.request)
        return context

class UserActivateView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'users.change_customuser'

    def post(self, request, customer_id, pk):
        user = get_object_or_404(User, pk=pk, customers=self.selected_customer)
        user.is_active = True
        user.save()
        messages.success(request, f"User {user.email} has been activated.")
        return redirect('users:user-list', customer_id=self.selected_customer.customer_id)

class UserDeactivateView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'users.change_customuser'

    def post(self, request, customer_id, pk):
        user = get_object_or_404(User, pk=pk, customers=self.selected_customer)
        user.is_active = False
        user.save()
        messages.success(request, f"User {user.email} has been deactivated.")
        return redirect('users:user-list', customer_id=self.selected_customer.customer_id)

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class UserResetPasswordView(SelectedCustomerRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'users.change_customuser'

    def get(self, request, customer_id, pk):
        user = get_object_or_404(User, pk=pk, customers=self.selected_customer)
        
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Construct reset URL
        reset_url = request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        )
        
        # Prepare email content
        subject = 'SCG Portal - Password Reset Request'
        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'SCG Portal'
        }
        message = render_to_string('users/password_reset/email.html', context)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        
        # Send email based on environment
        if settings.DEBUG:
            # In development, print to console
            print(f"Subject: {subject}")
            print(f"From: {from_email}")
            print(f"To: {recipient_list[0]}")
            print(f"Message:\n{message}")
        else:
            # In production, actually send the email
            send_mail(subject, message, from_email, recipient_list, html_message=message)
        
        messages.success(request, f'A password reset email has been sent to {user.email}.')
        return redirect('users:user-list', customer_id=self.selected_customer.customer_id)
    
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset/confirm.html'
    
    def get_success_url(self):
        messages.success(self.request, 'Your password has been successfully reset.')
        return reverse('login')