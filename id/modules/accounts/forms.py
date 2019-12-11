# -*- coding: utf-8 -*-
"""Accounts Forms."""

# Utils
import re

# Django
from django import forms
from django.utils.translation import ugettext as _

# Project
from id.models import (
    User, PasswordResetToken,
    TermAndCondition
)
from id.utils.validators import validate_birthdate


class RegisterForm(forms.Form):
    """Register Form."""

    gender = forms.ChoiceField(
        label='Sexo',
        choices=(('F', 'Femenino'), ('M', 'Masculino')),
        widget=forms.RadioSelect(
            attrs={'aria-required': 'true'}),
        required=True,
        error_messages={
            'required': 'Seleccioná tu Sexo.',
        }
    )

    first_name = forms.CharField(
        label='Nombres',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        error_messages={
            'required': 'Ingresá tu Nombre.',
        }
    )

    last_name = forms.CharField(
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        error_messages={
            'required': 'Ingresá tu Apellido.',
        }
    )

    birthdate = forms.DateField(
        label='Fecha de nacimiento',
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}),
        required=True,
        error_messages={
            'required': 'Ingresá tu Fecha de nacimiento.',
        }
    )

    country = forms.CharField(
        label='País de Residencia',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        error_messages={
            'required': 'Ingresá tu País de residencia',
        }
    )

    state = forms.CharField(
        label='Provincia',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
    )

    district = forms.CharField(
        label='Municipio',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
    )

    locality = forms.CharField(
        label='Localidad',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(
            attrs={'class': 'form-control',}),
        required=True,
        error_messages={
            'required': 'Ingresá tu Correo electrónico',
        }
    )

    email_confirmation = forms.EmailField(
        label='Confirmar Correo electrónico',
        widget=forms.EmailInput(
            attrs={'class': 'form-control',}),
        required=True,
        error_messages={
            'required': 'Ingresá la confirmación del Correo electrónico',
        }
    )

    password = forms.CharField(
        label='Creá una contraseña nueva para Mi Argentina',
        min_length=6,
        widget=forms.PasswordInput(
            attrs={'class': 'form-control'}),
        required=True,
        error_messages={
            'required': 'Ingresá tu Contraseña',
        }
    )

    def clean_email(self):
        """Check if email is already taken only when passport is selected."""
        email = self.cleaned_data['email']
        email_taken = User.objects.filter(email=email)
        if email_taken:
            raise forms.ValidationError(
                'El correo electrónico ya se encuentra registrado.')
        return email

    def clean_email_confirmation(self):
        """Email confimation match with email."""
        email_confirmation = self.data['email_confirmation']
        email = self.data['email']
        if email != email_confirmation:
            raise forms.ValidationError(
                'Los correos electrónicos no coinciden')
        return email_confirmation

    def clean_birthdate(self):
        """Birthdate validation."""
        birthdate = self.cleaned_data['birthdate']
        return validate_birthdate(birthdate)

    def clean_country(self):
        """When selected ARG require other location fields."""
        country = self.cleaned_data['country']
        if country == 'ARG':
            if 'state' in self.data:
                if not self.data['state']:
                    self.add_error('state', 'Ingresá tu Provincia.')
            if 'district' in self.data:
                if not self.data['district']:
                    self.add_error('district', 'Ingresá tu Municipio.')
            if 'locality' in self.data:
                if not self.data['locality']:
                    self.add_error('locality', 'Ingresá tu Localidad')
        return country


class PasswordResetForm(forms.Form):
    """Reset Password Form."""

    email = forms.EmailField(
        label='Ingresá tu correo electrónico para generar una nueva contraseña',
        widget=forms.EmailInput(
            attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Ingresá tu Correo electrónico',
        }
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if 'email' in self.changed_data:
            user_exist = User.objects.filter(email=email)
            if user_exist:
                user_exist.get().reset_password()
            else:
                raise forms.ValidationError(
                    'El correo electrónico que ingresaste no está registrado.')
        return email


class ChangePasswordForm(forms.Form):
    """Change password."""

    password = forms.CharField(
        label='Creá una contraseña nueva',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Ingresá la contraseña',
        }
    )
    password_confirmation = forms.CharField(
        label='Repetí la contraseña nueva',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Ingresá la confifmación de la contraseña',
        }
    )
    token = forms.CharField(required=False)

    def clean_password_confirmation(self):
        password_confirmation = self.cleaned_data['password_confirmation']
        password = self.data['password']
        if password != password_confirmation:
            self.add_error('password_confirmation',
                           'Asegurate de que las contaseñas coincidan.')
        else:
            token = self.data['token']
            # Check if token is valid
            valid_token = PasswordResetToken.objects.filter(token=token)
            if valid_token:
                token = valid_token.get()
                if not token.has_expired():
                    user = token.user
                    user.set_password(password)
                    user.save()
                    valid_token.delete()
                else:
                    self.add_error(
                        'token', 'El código para cambiar la contraseña ha expirado.')
            else:
                self.add_error(
                    'token', 'El código para cambiar la contraseña es incorrecto o ha expirado.')
        return password_confirmation


class ConfirmRegisterForm(forms.Form):
    """Confirm Register Form terms and conditions."""

    terms = forms.BooleanField(
        initial=True,
        widget=forms.CheckboxInput(),
        error_messages={
            'required': 'Aceptá los Términos y condiciones.',
        }
    )


class UpdateProfileForm(forms.ModelForm):
    """Update profile."""

    def __init__(self, *args, **kwargs):
        """Init method to get current user."""
        self.user = kwargs.pop('user', {})
        super(UpdateProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        """Meta class."""

        model = User
        fields = ['first_name', 'last_name', 'gender', 'birthdate',
                  'nationality', 'country', 'locality', 'street_name',
                  'street_number', 'appartment_floor', 'appartment_number',
                  'postal_code', 'email', 'phone_number']

    def clean_email(self):
        """Validate email."""
        email = self.cleaned_data['email']
        if 'email' in self.changed_data:
            if not email:
                raise forms.ValidationError("Debes ingresar un correo electrónico.")
            email_taken = User.objects.filter(email=email)
            if email_taken:
                raise forms.ValidationError(
                    _(u"El correo electrónico ya se encuentra registrado."))
        return email

    def clean_birthdate(self):
        """Validate birthdate."""
        birthdate = self.cleaned_data['birthdate']
        birthdate = validate_birthdate(birthdate)
        return birthdate

    def clean_phone_number(self):
        """Validate phone number."""
        phone_number = self.cleaned_data['phone_number']
        if 'phone_number' in self.changed_data:
            if '-' in phone_number:
                regex = "\+\w{1,3}-\w{2,4}-\w{5,8}"
                if re.search(regex, phone_number):
                    return phone_number
                else:
                    raise forms.ValidationError(
                        'El formato del número de teléfono ingresado es incorrecto')
        return phone_number


class TermsAndConditionForms(forms.Form):
    """Dynamic Terms and conditions Form."""

    def __init__(self, *args, **kwargs):
        """Form constructor dynamically."""
        self.user_terms = None
        if 'user' in kwargs:
            self.user = kwargs.pop('user')
            self.user_terms = kwargs.pop('user_terms')
        if 'terms' in kwargs:
            self.terms = kwargs.pop('terms')
        else:
            self.terms = TermAndCondition.objects.filter(is_principal=True).order_by('id')

        super(TermsAndConditionForms, self).__init__(*args, **kwargs)
        for term in self.terms:
            field_name = term.slug_name
            self.fields[field_name] = forms.BooleanField(required=False)
            self.fields[field_name].label = term.name
            # Instance existing terms
            if self.user_terms:
                user_selection_term = self.user_terms.get(term__slug_name=field_name)
                self.fields[field_name].initial = user_selection_term.is_active
            # Empty terms
            else:
                if field_name == 'general':
                    self.fields[field_name].initial = True
                else:
                    self.fields[field_name].initial = False
                    self.fields[field_name].required = False

    def general_field(self):
        """Return general terms field."""
        for field_name in self.fields:
            if field_name == 'general':
                yield self[field_name]

    def get_fields(self):
        """Return form fields except general term that is rendering in other section."""
        for field_name in self.fields:
            if field_name != 'general':
                yield self[field_name]

    def clean(self):
        """General validation."""
        data = super(TermsAndConditionForms, self).clean()
        if 'general' in data:
            if not data['general']:
                self.add_error(
                    'general',
                    'Tenés que aceptar los términos y condiciones generales.'
                )
        return data
