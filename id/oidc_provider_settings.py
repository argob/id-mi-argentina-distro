# -*- coding: utf-8 -*-

# Utils
from urllib.parse import (
    urlparse,
    parse_qs
)

# Django
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext as _

# Django OIDC Provider
from oidc_provider.models import Token
from oidc_provider.lib.claims import ScopeClaims

# Django REST Framework
from rest_framework_jwt.compat import get_username_field, get_username


def redirect_email_not_validated_hook(request, user, client):
    """Redirect if email is not validated."""

    if settings.MIAR_URL in parse_qs(request.META.get('QUERY_STRING'))['redirect_uri'][0] \
            and not user.email_verified:
        return redirect(reverse('accounts:send-email-activation'))


def custom_sub_generator(user):
    """Sobreescribe el valor sub del JWT."""
    return str(user.username)


class CustomScopeClaims(ScopeClaims):
    """Clase del scope para datos opcionales"""

    info_optional = (
        _(u'Datos opcionales'),
        _(u'Tus datos opcionales, número de dni, nacionalidad, etc.'),
    )

    def scope_optional(self):
        """Definición de los datos a mostrar en el scope opcional."""

        dic = {
            'username': self.user.username or "",
            'email': self.user.email or "",
            'dni_type': self.user.dni_type,
            'dni_number': self.user.dni_number,
            'nationality': {
                'code': getattr(self.user.nationality, 'code', ''),
                'name': getattr(self.user.nationality, 'name', ''),
            },
            'country': {
                'code': getattr(self.user.country, 'code', ''),
                'name': getattr(self.user.country, 'name', ''),
            },
            'locality': {
                'state': getattr(self.user.locality, 'state', ''),
                'name': getattr(self.user.locality, 'name', ''),
            },
            'province': {
                'state': (getattr(self.user.locality.district.province, 'pk', '')) if self.user.locality else '',
                'name': (getattr(self.user.locality.district.province, 'name', '')) if self.user.locality else '',
            },
            'district': {
                'state': (getattr(self.user.locality.district, 'pk', '')) if self.user.locality else '',
                'name': (getattr(self.user.locality.district, 'name', '')) if self.user.locality else '',
            },
            'street_name': self.user.street_name,
            'street_number': self.user.street_number,
            'postal_code': self.user.postal_code,
            'appartment_number': self.user.appartment_number,
            'appartment_floor': self.user.appartment_floor,
            'phone_number': self.user.phone_number,
            'email_verified': self.user.email_verified,
            'is_staff': self.user.is_staff
        }

        # Terms and conditions
        user_terms = self.user.usertermandcondition_set.all().order_by(
            'term', '-created').distinct('term')
        terms_dict = {}

        if user_terms:
            for user_term in user_terms:
                terms_dict[user_term.term.slug_name] = user_term.is_active

        dic['terms_and_conditions'] = terms_dict
        return dic


def userinfo(claims, user):
    """Se define los datos que quiero retornar en el endpoint userinfo."""

    claims['email'] = user.email
    claims['username'] = user.cuil
    claims['name'] = user.full_name
    claims['given_name'] = user.first_name
    claims['family_name'] = user.last_name
    claims['gender'] = user.gender
    claims['birthdate'] = user.birthdate.strftime('%d/%m/%Y')

    return claims


def default_idtoken_processing_hook(id_token, user, **kwargs):
    username = get_username(user)
    id_token['username'] = username
    id_token['email'] = user.email
    id_token['first_name'] = user.first_name
    id_token['last_name'] = user.last_name
    id_token['gender'] = user.gender
    id_token['birthdate'] = user.birthdate.strftime('%d/%m/%Y')
    id_token['dni_type'] = user.dni_type
    id_token['dni_number'] = user.dni_number

    return id_token
