from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, CustomGroup


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'type', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'customers')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'type')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Customers'), {'fields': ('customers',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active', 'customers')}
        ),
    )
    search_fields = ('email', 'customers__customer_name')
    ordering = ('email',)
    filter_horizontal = ('customers', 'groups', 'user_permissions')

    def get_customers(self, obj):
        return ", ".join([c.customer_name for c in obj.customers.all()])
    get_customers.short_description = 'Customers'

class CustomGroupAdmin(GroupAdmin):
    list_display = ('name', 'visibility')
    list_filter = ('visibility',)
    fieldsets = (
        (None, {'fields': ('name', 'permissions')}),
        (_('Visibility'), {'fields': ('visibility',)}),
    )

admin.site.unregister(Group)
admin.site.register(CustomGroup, CustomGroupAdmin)
admin.site.register(CustomUser, CustomUserAdmin)