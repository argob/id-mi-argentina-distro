"""ID Models."""

# Utils
import json
import logging
import random
import string
import uuid
import requests
from requests import HTTPError
from datetime import datetime, timedelta

# Django
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.postgres.fields import JSONField
from django.core import validators
from django.core.files.storage import FileSystemStorage
from django.urls import reverse_lazy
from django.contrib.sessions.models import Session
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete
from django.dispatch import receiver

# Project
import id.utils.validators as id_validators
from id.utils.emails import send_email

# Sentry
from raven.contrib.django.raven_compat.models import client


STATES = [
    ('CAB', u'Ciudad Autónoma de Buenos Aires'),
    ('BSA', u'Buenos Aires'), ('CAT', u'Catamarca'),
    ('COR', u'Córdoba'), ('CRR', u'Corrientes'), ('CHA', u'Chaco'),
    ('CHU', u'Chubut'), ('ENT', u'Entre Ríos'), ('FOR', u'Formosa'),
    ('JUJ', u'Jujuy'), ('PAM', u'La Pampa'), ('RIO', u'La Rioja'),
    ('MEN', u'Mendoza'), ('MIS', u'Misiones'), ('NEU', u'Neuquén'),
    ('RNE', u'Río Negro'), ('SAL', u'Salta'), ('SJU', u'San Juan'),
    ('SLU', u'San Luis'), ('SCR', u'Santa Cruz'), ('SFE', u'Santa Fe'),
    ('SDE', u'Santiago del Estero'), ('TDF', u'Tierra del Fuego'),
    ('TUC', u'Tucumán'),
]

GENDER = [
    ('F', _(u'Femenino')),
    ('M', _(u'Masculino')),
]

DNI = "DNI"
LE = "LE"
LC = "LC"

DNI_TYPES = [
    (DNI, _(u'DNI')),
    (LE, _(u'Libreta de Enrolamiento')),
    (LC, _(u'Libreta Cívica')),
]

ACCOUNT_DELETE_REASONS = [
    _(u'No entiendo para qué sirve'),
    _(u'No entiendo cómo funciona'),
    _(u'No quiero poner mis datos'),
    _(u'Otra razón'),
]

ACCOUNT_CREATORS = (
    (0, "Mi Argentina"),
)


class Country(models.Model):
    code = models.CharField(
        primary_key=True, max_length=3, verbose_name=_(u'Código'))
    name = models.CharField(max_length=150, verbose_name=_(u'Nombre'))

    class Meta:
        verbose_name = _(u'País')
        verbose_name_plural = _(u'Países')

    def __str__(self):
        return u'{0}'.format(self.name)


class Province(models.Model):
    """Provincia."""
    name = models.CharField(max_length=150, verbose_name=_(u'Nombre'))

    class Meta:
        verbose_name = _(u'Provincia')
        verbose_name_plural = _(u'Provincias')

    def __str__(self):
        return u'{}'.format(self.name)


class District(models.Model):
    """Departamento."""
    name = models.CharField(max_length=150, verbose_name=_(u'Nombre'))
    province = models.ForeignKey(Province, verbose_name=_(
        u'Provincia'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _(u'Departamento')
        verbose_name_plural = _(u'Departamentos')

    def __str__(self):
        return u'{}'.format(self.name)


class Locality(models.Model):
    state = models.CharField(
        max_length=3, choices=STATES, verbose_name=_(u'Provincia'))
    name = models.CharField(max_length=150, verbose_name=_(u'Nombre'))
    district = models.ForeignKey(District, null=True, verbose_name=_(
        u'Departamento'), on_delete=models.CASCADE)
    updated = models.BooleanField(default=False)

    class Meta:
        verbose_name = _(u'Localidad')
        verbose_name_plural = _(u'Localidades')

    def __str__(self):
        return u'{0}'.format(self.name)


class User(AbstractUser):
    email = models.EmailField(
        'correo electronico',
        unique=True,
        error_messages={
            'unique': 'El correo ya se encuentra registrado.'
        }
    )
    gender = models.CharField(
        max_length=1, choices=GENDER, verbose_name=_(u'Genero'))
    birthdate = models.DateField(verbose_name=_(u'Fecha de Nacimiento'))
    dni_type = models.CharField(
        max_length=100, blank=True, default='', choices=DNI_TYPES, verbose_name=_(u'Tipo Documento'))
    dni_number = models.CharField(
        max_length=60, blank=True, default='', verbose_name=_(u'Número Documento'))
    nationality = models.ForeignKey(
        Country, null=True, blank=True, verbose_name=_(u'Nacionalidad'), on_delete=models.SET_NULL)
    country = models.ForeignKey(
        Country, null=True, blank=True, related_name='current_country', verbose_name=_(u'País'), on_delete=models.SET_NULL)
    locality = models.ForeignKey(
        Locality, null=True,blank=True,verbose_name=_(u'Localidad'),on_delete=models.SET_NULL)
    street_name = models.CharField(
        max_length=200, blank=True, default='', verbose_name=_(u'Nombre Calle'))
    street_number = models.CharField(
        max_length=20, blank=True, default='', validators=[
            validators.RegexValidator(r'^[0-9]{1,20}$', _(u'Número calle inválido.'))
        ], verbose_name=_(u'Número Calle'))
    postal_code = models.CharField(
        max_length=12, blank=True, default='', verbose_name=_(u'Código Postal'))
    appartment_number = models.CharField(
        max_length=20, blank=True, default='', verbose_name=_(u'Nombre Departamento'))
    appartment_floor = models.CharField(
        max_length=20, blank=True, default='', verbose_name=_(u'Piso Departamento'))
    phone_number = models.CharField(
        max_length=60, blank=True, default='', verbose_name=_(u'Teléfono Movil'))
    email_verified = models.BooleanField(
        default=False, verbose_name=_(u'Email Verificado'))
    created_by = models.IntegerField(verbose_name=_(
        u"Creado por"), default=0, choices=ACCOUNT_CREATORS)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'gender', 'birthdate']

    class Meta:
        ordering = ['-date_joined']
        verbose_name = _(u'Usuario')
        verbose_name_plural = _(u'Usuarios')
        permissions = (
            ('read_user', 'Can read Usuario'),
        )

    def __str__(self):
        return u'{0}'.format(self.id)

    def reset_password(self):
        # Generate the token.
        token = PasswordResetToken.create(user=self)
        token.save()

        send_email(
            self.email,
            _(u'Cambiá tu contraseña'),
            'password_reset.html',
            {
                'first_name': self.first_name,
                'reset_url': token.get_absolute_url()
            },
            ['usuario-recupera-contrasena',]
        )

    def send_email_changed(self):
        token, created = EmailActivationToken.objects.get_or_create(user=self)

        if not token:
            logger.error('Envío de token vacío al cambiar el mail. Token')

        params = {
            "activation_url": token.get_absolute_url(),
            "next": settings.MIAR_URL
        }

        # Send activation email to user
        send_email.delay(
            self.email,
            _(u'Activá tu cuenta de Mi Argentina.'),
            'send_email_changed.html',
            params,
            ['usuario-cambia-mail',]
        )

    @staticmethod
    def create_id_user(data):
        """create user with clean data"""

        # prepare data to be storaged in user model
        if 'country' in data.keys() and data['country']:
            data['country_id'] = Country.objects.filter(
                pk=data['country']).first().code
            data.pop('country', None)

        if 'nationality' in data.keys() and data['nationality']:
            data['nationality'] = Country.objects.filter(
                code=data['nationality']).first()

        if 'locality' in data.keys():
            # check locality existence
            try:
                data['locality'] = Locality.objects.filter(
                    pk=data['locality']).first()
            except:
                data.pop('locality', None)

        user = User()
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.email = data['email']
        user.username = data['email']
        user.gender = data['gender']
        user.birthdate = data['birthdate']
        user.set_password(data['password'])
        user.last_login = timezone.now()
        user.is_active = True
        user.save()
        user.send_activation_email()

        return user

    def resend_activation_email(self, next_url=None):
        token = EmailActivationToken.create(user=self)
        token.save()

        params = dict()
        params["activation_url"] = token.get_absolute_url()

        params["next"] = settings.MIAR_URL

        send_email.delay(
            self.email,
            _(u'Activá tu cuenta de Mi Argentina.'),
            'resend_email_activation.html',
            params,
            ['usuario-solicita-activacion-mail',]
        )

    def send_activation_email(self, next_url=None, email=None):
        """Send activation email to user
        [parameters]
        email = if comes this parameter, the email will be sent to there
        """
        token = EmailActivationToken.create(user=self)
        token.save()

        to_email = email if email else self.email

        send_email(
            self.email,
            _(u'Activá tu cuenta.'),
            'email_activation.html',
            {
                'first_name': self.first_name,
                'id_number': self.username,
                'activation_url': token.get_absolute_url(),
                'next': next_url
            },
            ['usuario-crea-cuenta',]
        )

    @staticmethod
    def _check_email(user, email):
        qs = User.objects.filter(email=email).exclude(id=user.id)
        # Chequear que no este el mismo mail verificado
        for user in qs:
            if user.email_verified:
                return False

        # Chequear que un usuario no tengo un link de reset vigente
        for token in EmailActivationToken.objects.filter(user__email=email).exclude(user=user):
            if not token.has_expired():
                return False

        return True

    @property
    def full_name(self):
        name = u''
        if self.first_name:
            name = u'{0}'.format(self.first_name)
            if self.last_name:
                name += u' {0}'.format(self.last_name)
        return name


class UserToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=150)
    date_sent = models.DateTimeField(
        auto_now=True, verbose_name=_(u'Fecha de Envío'))

    class Meta:
        abstract = True
        ordering = ['-date_sent']

    def __str__(self):
        return u'{0}'.format(self.token)

    @classmethod
    def create(cls, user):
        defaults = {
            "token": uuid.uuid4().hex.upper(),
            "date_sent": datetime.now()
        }
        obj, _ = cls.objects.update_or_create(user=user, defaults=defaults)
        return obj

    def has_expired(self):
        return timezone.now() > (self.date_sent + timedelta(hours=3))


class EmailActivationToken(UserToken):
    class Meta(UserToken.Meta):
        verbose_name = _(u'Token Activación de Email')
        verbose_name_plural = _(u'Tokens Activación de Email')

    def get_absolute_url(self):
        return reverse_lazy('accounts:email-activation') + '?token=' + self.token


class PasswordResetToken(UserToken):
    class Meta(UserToken.Meta):
        verbose_name = _(u'Token de Contraseña')
        verbose_name_plural = _(u'Tokens de Contraseñas')

    def get_absolute_url(self):
        return reverse_lazy('accounts:password-reset') + '?token=' + self.token


class TermAndCondition(models.Model):
    """Terms and Conditions Model."""

    name = models.CharField('Term name', max_length=140)
    slug_name = models.SlugField(unique=True, max_length=100)
    is_principal = models.BooleanField(
        'Principal',
        default=True,
    )
    users = models.ManyToManyField(
        'User', through='UserTermAndCondition',
        through_fields=('term', 'user')
        )

    class Meta:
        """Meta class."""

        verbose_name = "Términos y Condiciones."
        verbose_name_plural = "Términos y condiciones"

    def __str__(self):
        """Return Term slug name."""
        return self.slug_name


class UserTermAndCondition(models.Model):
    """User and Terms and Conditions Models relation."""

    user = models.ForeignKey('User', on_delete=models.CASCADE)
    term = models.ForeignKey('TermAndCondition', on_delete=models.CASCADE)
    is_active = models.BooleanField(
        default=False,
        help_text='Term and condition acceptance.'
    )

    created = models.DateTimeField(
        'created at',
        auto_now_add=True,
        help_text='Date time on which the object was created.'
    )
    modified = models.DateTimeField(
        'modified at',
        auto_now=True,
        help_text='Date time on which the object was last modified.'
    )

    class Meta:
        """Meta class."""

        verbose_name = "Términos y Condiciones de Usuario"
        verbose_name_plural = "Términos y condiciones de Usuarios"

    def __str__(self):
        """Return slugname and status."""
        return 'slug: {} | status:{}'.format(self.term.slug_name, self.is_active)
