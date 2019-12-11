"""General Validators """

# Utils
import string
from datetime import datetime
from re import match

# Django
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.utils import timezone

# Project
import id.models


def validate_email_change(old_email, new_email):
    """Validate change on email"""
    response = {}
    if old_email != new_email:
        email_taken = id.models.User.objects.filter(email=new_email)
        if email_taken:
            response['error'] = 'El email ya se encuentra registrado'
        else:
            response['valid_email'] = True
    return response

def validate_birthdate(birthdate):
    """Validate that users had mayor than 13 years old"""
    this_year = timezone.now().year
    if not (this_year - birthdate.year) > 12:
        raise ValidationError(
            'Tenes que ser mayor de 13 años para poder registrarte.')
    if (birthdate.year < 1900):
        raise ValidationError('El año ingresado es incorrecto.')
    return birthdate

def validate_dni_number(dni):
    try:
        dni = int(dni)
    except ValueError:
        raise ValidationError("El DNI debe ser un numero")

def validate_date(date_str):
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').date()
    except:
        raise ValidationError(
            _(u'La fecha es incorrecta. Debe tener el formato DD/MM/AAAA.'))

def validate_password(password, password_again):
    error = None
    if (len(password) < 7):
        error = _(u'La contraseña debe tener al menos 7 caracteres.')
    if not (password == password_again):
        error = _(u'Las contraseñas que ingresaste deben ser iguales.')

    if error:
        raise ValidationError(error)

def validate_password_length(password):
    if (len(str(password)) < 7):
        raise ValidationError(
            _(u'La contraseña debe tener al menos 7 caracteres.'))
    return password

def validate_phone(phone):
    if not match(r'^(\d){3}(\d){0,2}-15(\d){6}(\d){0,2}$', phone):
        raise ValidationError(_(u'El número teléfonico es incorrecto.'))
