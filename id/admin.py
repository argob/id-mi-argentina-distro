"""ID admin."""

# Django
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

# Project
from id.models import (
    User,
    EmailActivationToken,
    PasswordResetToken,
    TermAndCondition,
    UserTermAndCondition,
    Country,
    Province,
    District,
    Locality
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User admin."""
    list_display = ['id', 'email', 'email_verified', 'first_name', 'last_name', 'date_joined']
    list_display_links = ('id', 'email')
    search_fields = ['email', 'username', 'first_name', 'last_name']
    fieldsets = [
        [_(u'DATOS OBLIGATORIOS'), {
            'fields': ('first_name', 'last_name', 'gender', 'birthdate', 'email', 'username'),
        }],
        [_(u'DATOS OPCIONALES'), {
            'fields': ('dni_type', 'dni_number', 'nationality', 'country', 'locality', 'postal_code', 'street_name', 'street_number', 'appartment_number', 'appartment_floor', 'phone_number'),
        }],
        [_(u'INFORMACIÓN DE LA CUENTA'), {
            'fields': ('is_active', 'email_verified', 'last_login', 'date_joined'),
        }],
        [_(u'PERMISOS'), {
            'fields': ('is_staff', 'is_superuser', 'groups'),
        }],
    ]


admin.site.register(EmailActivationToken)
admin.site.register(PasswordResetToken)
admin.site.register(TermAndCondition)
admin.site.register(UserTermAndCondition)
admin.site.register(Country)
admin.site.register(Province)
admin.site.register(District)
admin.site.register(Locality)
