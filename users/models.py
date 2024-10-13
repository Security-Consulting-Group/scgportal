from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from customers.models import Customer
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('type', CustomUser.UserType.STAFF)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    class UserType(models.TextChoices):
        MULTI_ACCOUNT = 'multi_account', _('Multi Account')
        STAFF = 'staff', _('Staff')
        NORMAL = 'normal', _('Normal')

    username = None
    email = models.EmailField(_('email address'), unique=True)
    customers = models.ManyToManyField(Customer, related_name='users', blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.NORMAL,
        verbose_name=_('User Type')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        permissions = [
            ("view_customer_user", "Can view users in the same customer group"),
            ("change_customer_user", "Can change users in the same customer group"),
            ("add_customer_user", "Can add users to the same customer group"),
        ]

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        if self.pk:  # Only check for existing users
            if self.type == self.UserType.NORMAL and self.customers.count() > 1:
                raise ValidationError(_("Normal users can only be assigned to one customer. Please change the user type to 'Multi Account' if multiple customers are needed."))

    def save(self, *args, **kwargs):
        if not self.pk:  # For new users
            super().save(*args, **kwargs)  # Save first to get a primary key
            if self.type == self.UserType.NORMAL and self.customers.count() > 1:
                raise ValidationError(_("Normal users can only be assigned to one customer."))
        else:
            self.full_clean()  # For existing users, run full validation
            super().save(*args, **kwargs)

    @customer.setter
    def customer(self, value):
        """
        For backwards compatibility, set the customer using the old single-customer field.
        """
        if value is None:
            self.customers.clear()
        else:
            self.customers.set([value])
            
    def get_customers(self):
        return self.customers.all()

    def get_default_customer(self):
        """
        Returns the default customer for the user.
        For NORMAL users, this will be their only customer.
        For MULTI_ACCOUNT and STAFF users, this will be the first customer in their list.
        """
        return self.customers.first()