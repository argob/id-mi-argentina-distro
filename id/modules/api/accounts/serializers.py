"""Account API serializers."""

# Django
from id.utils.validators import validate_email_change
from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.contrib.auth import password_validation

# Django REST Framework
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    Serializer, CharField, ChoiceField,
    DateField, EmailField, BooleanField,
    ModelSerializer
)
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.compat import PasswordField, get_username_field

# Project
from id.models import (
    GENDER, User, Country, Province,
    Locality, District,
    UserTermAndCondition, TermAndCondition
)

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class PasswordResetSerializer(Serializer):
    """Serializer for password reset."""

    email = EmailField(required=True)

    def update(self, instance, validated_data):
        pass

    def validate_email(self, value):
        user = User.objects.filter(email=value).first()

        if not user:
            raise ValidationError(
                _(u'El correo electrónico que ingresaste no está registrado.'))

        return value

    def create(self, validated_data):
        """
        Sends reset password email to user

        :param validated_data:
        :return:
        """

        user = User.objects.filter(email=validated_data["email"]).first()
        user.reset_password()

        return True


class PasswordChangeSerializer(Serializer):
    """Change password serializer."""

    password = serializers.CharField(min_length=6)
    new_password = serializers.CharField(min_length=6)
    new_password_confirmation = serializers.CharField(min_length=6)

    def validate_password(self, value):
        """Check that the password is valid for current user."""
        user = self.context.get('user')
        password = value
        user_auth = authenticate(
            username=user.username,
            password=password
        )
        if not user_auth:
            raise serializers.ValidationError("Contraseña actual incorrecta.")
        return value

    def validate(self, data):
        """Verify passwords match."""
        old_passwd = data['password']
        passwd = data['new_password']
        passwd_conf = data['new_password_confirmation']
        if passwd != passwd_conf:
            raise serializers.ValidationError("Contraseñas no coinciden.")
        if old_passwd == passwd:
            raise serializers.ValidationError(
                "Nueva contraseña debe ser diferente a la antigua.")
        password_validation.validate_password(passwd)
        return data

    def create(self, data):
        """Handle user and change password."""
        user = self.context.get('user')
        password = self.data.get('new_password')
        user.set_password(password)
        user.save()
        return user


class DistrictSerializer(ModelSerializer):
    class Meta:
        model = District
        fields = ('id', 'name', 'province')


class LocalitySerializer(ModelSerializer):
    class Meta:
        model = Locality
        fields = ('id', 'state', 'name', 'district')


class ProvinceSerializer(ModelSerializer):
    class Meta:
        model = Province
        fields = ('id', 'name')


class CountrySerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = ('code', 'name')


class RegisterSerializer(Serializer):
    """Register serializer, is used to register new accounts."""

    first_name = CharField(required=True)
    last_name = CharField(required=True)
    gender = ChoiceField(choices=GENDER, required=True)
    birthdate = DateField(required=True, input_formats=["%d/%m/%Y"])
    email = EmailField(required=True)
    password = CharField(required=True)

    def validate_birthdate(self, value):
        this_year = timezone.now().year
        if not (this_year - value.year) > 12:
            raise ValidationError(
                _(u'Tenes que ser mayor de 13 años para poder registrarte.'))
        if (value.year < 1900):
            raise ValidationError(_(u'El año ingresado es incorrecto.'))
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).only('email').exists():
            raise ValidationError(
                _(u'El correo electrónico ya se encuentra registrado.'))

        return value

    def validate_first_name(self, value):
        if any(char.isdigit() for char in value):
            raise ValidationError(_(u'Tu nombre contiene números.'))
        elif len(value) > 30:
            raise ValidationError(_(u'Tu nombre es demasiado largo.'))
        return value

    def validate_last_name(self, value):
        if any(char.isdigit() for char in value):
            raise ValidationError(_(u'Tu apellido contiene números.'))
        elif len(value) > 30:
            raise ValidationError(_(u'Tu apellido es demasiado largo.'))
        return value

    def create(self, validated_data):
        # Create and store the user.
        return User.create_id_user(validated_data)


class RegisterV2Serializer(RegisterSerializer):
    """Version 2 register serializer."""

    email_confirmation = EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super(RegisterV2Serializer, self).__init__(*args, **kwargs)
        self.context['terms'] = TermAndCondition.objects.filter(is_principal=True).order_by('id')
        for term in self.context['terms']:
            field_name = term.slug_name
            self.fields[field_name] = serializers.BooleanField()

    def validate_email_confirmation(self, data):
        if data != self.initial_data['email']:
            raise ValidationError('Los correos electrónicos no coinciden.')
        return data

    def validate(self, data):
        """Validate input data terms and aconditions."""
        if not data['general']:
            raise ValidationError({'general': 'General term is required.'})

        data_validated = RegisterSerializer.validate(self, data)
        return data_validated

    def create(self, data):
        data.pop('email_confirmation')
        user = RegisterSerializer.create(self, data)
        for term in self.context['terms']:
            if term.slug_name in data:
                user.usertermandcondition_set.create(
                    term=term,
                    is_active=data[term.slug_name]
                )

        return user


class RegisterV3Serializer(RegisterV2Serializer):
    """Register V3 that contains province and locality data."""

    country = serializers.CharField(
        required=True,
        max_length=10
        )
    locality = serializers.CharField(
        max_length=10,
        required=False
    )

    def validate_country(self, data):
        """Validate country code."""
        country = Country.objects.filter(code=data)
        if not country:
            raise ValidationError('Country code does not exist.')
        return data

    def validate_locality(self, data):
        """Validate locality id when country selected is [ARG]."""
        country = self.initial_data['country']
        if country == 'ARG':
            locality = Locality.objects.filter(id=data)
            if not locality:
                raise ValidationError('Locality id does not exist.')
        return data

    def validate(self, data):
        """Validate input data."""
        validated_data = RegisterV2Serializer.validate(self, data)
        return validated_data

    def create(self, data):
        """Create user."""
        user = RegisterV2Serializer.create(self, data)
        return user


class UserSerializer(ModelSerializer):
    """User Profile data."""

    # Add extra fields for oidc data
    given_name = serializers.CharField(source='first_name', read_only=True)
    family_name = serializers.CharField(source='last_name', read_only=True)
    name = serializers.SerializerMethodField('name_field')

    # Custom format
    birthdate = DateField(
        required=True, format='%Y-%m-%dT%H:%M:%S.%f', input_formats=['%d/%m/%Y'])
    locality_name = CharField(source='locality.name', read_only=True)
    district_name = CharField(source='locality.district.name', read_only=True)
    province_name = CharField(
        source='locality.district.province.name', read_only=True)
    nationality_name = CharField(source='nationality.name', read_only=True)
    country_name = CharField(source='country.name', read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'given_name', 'family_name', 'name', 'gender', 'birthdate',
            'dni_type', 'dni_number', 'nationality', 'country', 'locality', 'street_name', 'street_number',
            'appartment_number', 'appartment_floor', 'postal_code', 'phone_number', 'locality_name', 'district_name',
            'province_name', 'nationality_name', 'country_name', 'email_verified'
        )
        read_only_fields = ('email', 'username', 'email_verified')

    def name_field(self, user):
        """Extra field for oidc data that return user full name."""
        return '{} {}'.format(user.first_name, user.last_name)

    def validate_email(self, email):
        """Validate email changes."""
        user = self.instance
        response = validate_email_change(user.email, email)
        if 'error' in response:
            raise ValidationError(response['error'])
        elif 'valid_email' in response:
            user.send_activation_email(email=email)
        return email


class JSONWebTokenSerializer(Serializer):
    """
    Serializer para validar los campos 'username' y 'password'.

    'username' está definido en UserModel.USERNAME_FIELD.

    Retorna un JWT para usar como autenticación en el resto de los endpoints que lo requieran.
    """

    def __init__(self, *args, **kwargs):
        """Se agrega dinámicamente USERNAME_FIELD a self.fields."""
        super(JSONWebTokenSerializer, self).__init__(*args, **kwargs)

        self.fields[self.username_field] = CharField()
        self.fields['password'] = PasswordField(write_only=True)

    @property
    def username_field(self):
        return get_username_field()

    def validate(self, attrs):
        """
        Validations
        :param attrs:
        :return:
        """
        username = attrs.get(self.username_field)

        credentials = {
            self.username_field: username,
            'password': attrs.get('password')
        }

        if not all(credentials.values()):
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise ValidationError(msg)

        user = authenticate(**credentials)

        if user:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise ValidationError(msg)

            payload = jwt_payload_handler(user)

            return {
                'token': jwt_encode_handler(payload),
                'user': user
            }
        msg = _('Unable to log in with provided credentials.')
        raise ValidationError(msg)


class EmailActivationSerializer(Serializer):

    def validate(self, cleaned_data):
        user = self.context['user']
        if user.is_active is False or user.enable is False:
            raise ValidationError("El usuario no esta activo")
        if user.email in ["", None]:
            raise ValidationError("El usuario no tiene un email valido")
        if user.email_verified is True:
            raise ValidationError("El usuario ya valido el mail")

        return cleaned_data

    def save(self):
        self.context['user'].send_activation_email()


class TermAndConditionsModelSerializer(ModelSerializer):
    """Term and conditions model serializer"""
    term = CharField(source='term.slug_name')
    is_active = serializers.BooleanField()
    title = serializers.CharField(source='term.name')

    class Meta:
        """Meta class"""
        model = UserTermAndCondition
        exclude = ('user', 'id', 'modified')
        read_only_fields = (
            'created',
        )


class CreateUserTermAndConditionSerializer(Serializer):
    """Create user terms and conditions."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def __init__(self, *args, **kwargs):
        """Handle serializer instance."""
        super(CreateUserTermAndConditionSerializer, self).__init__(*args, **kwargs)
        self.context['terms'] = TermAndCondition.objects.all().order_by('id')
        for term in self.context['terms']:
            field_name = term.slug_name
            self.fields[field_name] = serializers.BooleanField()

    def validate(self, data):
        """Validate input data."""
        if not data['general']:
            raise ValidationError({'general': 'General term is required.'})
        if data['disability'] and not data['health']:
            raise ValidationError({'health': 'Health term is required to check disability field.'})
        return data

    def create(self, data):
        """Create user's term and condition."""
        user = self.context['user']
        data.pop('user')
        user_terms = self.context['user_terms']
        terms = self.context['terms']
        # Check terms changed (Update 'similar')
        if user_terms:
            for user_term in user_terms:
                slug_name = user_term.term.slug_name
                # Update only changed terms.
                if data[slug_name] != user_term.is_active:
                    # get current term object
                    term = terms.get(slug_name=slug_name)
                    user.usertermandcondition_set.create(
                        term=term,
                        origin='MOBILE',
                        is_active=data[slug_name]
                    )
        else:
            # Create all terms (first_time)
            for term in self.context['terms']:
                if term.slug_name in data:
                    user.usertermandcondition_set.create(
                            term=term,
                            origin='MOBILE',
                            is_active=data[term.slug_name]
                        )

        updated_terms = user.usertermandcondition_set.filter(
            term__is_principal=True)\
            .order_by(
            'term',
            '-created')\
            .distinct('term')
        return updated_terms
