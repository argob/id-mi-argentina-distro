# -*- encoding: utf8 -*-
"""ID principal Forms"""

#Django
from django import forms
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.contrib.auth import authenticate

#Project
from id.models import User


class LoginForm(forms.Form):
    """Custom Login Form"""
    email = forms.EmailField(
        max_length=64,
        label='Correo electrónico',
        error_messages={
            'required': 'Ingresá tu correo electrónico.',
        }
    )

    password = forms.CharField(
        label='Password',
        error_messages={
            'required': 'Ingresá tu contraseña.',
        }
    )

    error_messages = {
        'invalid_login': _(
            "El correo electrónico o la contraseña ingresada es incorrecta."
        ),
    }

    def __init__(self, request, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validation for cuil number"""
        data = super().clean()
        email = self.data['email']
        password = self.data['password']

        if not self.errors:
            user = User.objects.only('email').filter(
                (Q(email=email)) & Q(is_active=True)
            )

            if not user:
                raise self.get_invalid_login_error()
            else:
                if password:
                    self.user_cache = authenticate(
                        self.request, username=user.get().username, password=password)
                    if self.user_cache is None:
                        raise self.get_invalid_login_error()
                else:
                    self.confirm_login_allowed(self.user_cache)
        return self.data

    def get_user(self):
        return self.user_cache

    def get_invalid_login_error(self):
        return forms.ValidationError(
            self.error_messages['invalid_login'],
            code='invalid_login'
        )


class CustomSetPasswordForm(forms.Form):
    """Set password Form."""
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
    token = forms.CharField(required=False,widget=forms.HiddenInput, )

    def clean_password_confirmation(self):
        password_confirmation = self.cleaned_data['password_confirmation']
        password = self.data['password']
        if password != password_confirmation:
            self.add_error(
                'password_confirmation',
                'Asegurate de que las contaseñas coincidan.')
        return password_confirmation
