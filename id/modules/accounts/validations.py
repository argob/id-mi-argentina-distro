# -*- coding: utf-8 -*-
"""Accounts validations"""

# Django
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import ugettext as _

# Project
from id.models import User


def validate_update_email(new_email):
    user_qs = User.objects.only('email')
    errors = {
        'data': new_email,
    }

    if user_qs.filter(email=new_email).exists():
        errors['email'] = _(
            u'El correo electrónico ya se encuentra registrado.')

    try:
        if not len(new_email) > 0:
            errors['email'] = _(u'Falta ingresar este dato.')
        else:
            validate_email(new_email)
    except ValidationError:
        errors['email'] = _(
            u'El correo electrónico no es válido, por favor intentá de nuevo.')

    return errors
