"""Accounts API views."""

# Utils
import logging
from datetime import datetime

# Django
from django.contrib.auth import logout
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator

# Django rest framework
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import mixins, viewsets, status
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework import status

# JWT
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import JSONWebTokenAPIView

# Django OIDC Provider
from oidc_provider.lib.utils.oauth2 import protected_resource_view

# Project
from id.authentication import BearerTokenAuthentication
from id.utils.emails import send_email
from id.modules.api.permissions import IsAccountOwner
from id.models import (
    Country, Province,
    District, Locality,
    TermAndCondition,
    UserTermAndCondition)
from id.modules.api.accounts.serializers import (
    RegisterSerializer, UserSerializer, CountrySerializer,
    ProvinceSerializer, DistrictSerializer, LocalitySerializer,
    PasswordResetSerializer, JSONWebTokenSerializer,
    EmailActivationSerializer, RegisterV2Serializer,
    TermAndConditionsModelSerializer,
    CreateUserTermAndConditionSerializer,
    RegisterV3Serializer, PasswordChangeSerializer
)


jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

logger = logging.getLogger()
User = get_user_model()


class LoginView(JSONWebTokenAPIView):
    """
    API View that receives a POST with a user's username and password.

    Returns a JSON Web Token that can be used for authenticated requests.
    """
    serializer_class = JSONWebTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data.get('user') or request.user
            token = serializer.validated_data.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response(response_data)

            # Update last login
            User.objects.filter(id=user.id).update(last_login=datetime.now())

            if api_settings.JWT_AUTH_COOKIE:
                expiration = (
                    datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)
            return response
        else:
            if "non_field_errors" in serializer.errors.keys():
                return Response({
                    "error": True,
                    "message": "Usuario o clave incorrecta"
                }, status=status.HTTP_200_OK)
            elif "email" in serializer.errors.keys() or "password" in serializer.errors.keys():
                return Response({
                    "error": True,
                    "message": "Los campos email y password son requeridos"
                }, status=status.HTTP_400_BAD_REQUEST)


class LogoutViewView(APIView):
    """User logout view."""
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        # Logout session
        logout(request)
        return Response({
            "error": False,
            "messages": None,
            "result": None
        }, status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    """Reset password view."""
    permission_classes = (AllowAny, )

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "error": False,
                "messages": None,
                "result": None
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": True,
                "messages": serializer.errors,
                "result": None
            }, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    """Change password View."""
    authentication_classes = (BearerTokenAuthentication,)
    permission_classes = (IsAuthenticated, IsAccountOwner)

    def post(self, request):
        user = self.request.user
        context = {'user': user}
        serializer = PasswordChangeSerializer(
            data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = {'message': 'Contraseña modificada con éxito.'}
        return Response(data, status=status.HTTP_200_OK)


class CountryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CountrySerializer
    permission_classes = (IsAuthenticated, )
    queryset = Country.objects.all()


class ProvinceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ProvinceSerializer
    permission_classes = (IsAuthenticated, )
    queryset = Province.objects.all()


class DistrictViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = DistrictSerializer
    permission_classes = (IsAuthenticated, )
    queryset = District.objects.all()


class LocalityViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = LocalitySerializer
    permission_classes = (IsAuthenticated, )
    queryset = Locality.objects.all()


class RegisterView(CreateModelMixin, GenericViewSet):
    """Register view."""

    permission_classes = (AllowAny, )
    serializer_class = RegisterV3Serializer

    def create(self, request):
        """Create user."""
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            data = {
                "error": False,
                "messages": None,
                "result": {"token": token}
            }
        else:
            data = {
                "error": True,
                "messages": serializer.errors,
                "result": None
            }

        return Response(data, status=status.HTTP_200_OK)


class MeViewSet(mixins.ListModelMixin,
                mixins.UpdateModelMixin,
                mixins.RetrieveModelMixin,
                mixins.DestroyModelMixin,
                viewsets.GenericViewSet):
    """Profile Viewset."""
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        instance = request.user
        serializer = self.get_serializer(instance, many=False)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.request.user
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def delete(self, request, pk=None):
        user = self.request.user
        user.delete()
        send_email(user.email,
                   "Borraste tu cuenta de Mi Argentina.",
                   'account_deleted.html')
        data = {'message': 'Account deleted.'}
        return Response(data, status=status.HTTP_200_OK)


class ActivationEmailView(APIView):
    """Envia el email de activacion"""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = EmailActivationSerializer(
            data={},
            context={"user": request.user}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "result": {},
                "error": False,
                "message": "El email ha sido enviado"
            })
        else:
            return Response({
                "result": serializer.errors,
                "error": True,
                "message": "Error al enviar el email"
            }, status=400)


class V2ActivationEmailView(APIView):
    """Envia el email de activacion."""
    authentication_classes = (BearerTokenAuthentication,)
    permission_classes = (IsAuthenticated, IsAccountOwner)

    def post(self, request):
        serializer = EmailActivationSerializer(
            data={},
            context={"user": request.user}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "result": {},
                "error": False,
                "message": "El email ha sido enviado"
            })
        else:
            return Response({
                "result": serializer.errors,
                "error": True,
                "message": "Error al enviar el email"
            }, status=400)


class TermAndConditionsViewset(mixins.ListModelMixin,
                               mixins.CreateModelMixin,
                               viewsets.GenericViewSet):
    """Terms and conditions viewset."""

    def dispatch(self, request, *args, **kwargs):
        """Get terms and conditions."""
        self.terms = TermAndCondition.objects.all().order_by('id')
        return super(TermAndConditionsViewset, self).dispatch(request, *args, **kwargs)

    def get_serializer_class(self):
        """Return serializer based on action."""
        if self.action == 'create':
            return CreateUserTermAndConditionSerializer

        return TermAndConditionsModelSerializer

    def get_queryset(self):
        """Return terms and conditions."""
        self.user = self.request.user
        if self.action == 'digital_dni':
            try:
                self.user_terms = self.user.usertermandcondition_set.filter(
                    term__is_principal=False).last()
            except UserTermAndCondition.DoesNotExist:
                self.user_terms = None

        else:
            self.user_terms = self.user.usertermandcondition_set.filter(
                term__is_principal=True)\
                .order_by('term', '-created')\
                .distinct('term')
            # Some accounts have two or less terms and condition selected
            # and there will be cleaned to select three.
            if len(self.user_terms) < 3:
                self.user_terms.delete()
        return self.user_terms

    def get_serializer_context(self):
        """Add user to a serializer context."""
        context = super(TermAndConditionsViewset, self).get_serializer_context()
        context['user'] = self.request.user
        if self.action == 'digital_dni':
            self.terms = self.terms.filter(is_principal=False)
        else:
            self.terms = self.terms.filter(is_principal=True)

        context['terms'] = self.terms

        if 'user_terms' not in dir(self):
            context['user_terms'] = self.get_queryset()
        else:
            context['user_terms'] = self.user_terms

        return context

    def empty_response(self, terms):
        """Empty response for terms to indicate that user
        have not selected its term(s)."""
        response = []
        for term in terms:
            data = {
                "term": term.slug_name,
                "is_active": '',
                "title": term.name,
                "created": '',
                }

            response.append(data)
        if len(response) < 2:
            return response[0]
        return response

    def list(self, request, *args, **kwargs):
        """Get method."""
        queryset = self.filter_queryset(self.get_queryset())
        if not queryset:
            # Empty terms from db
            term = self.terms.filter(is_principal=True)
            response = self.empty_response(term)
            return Response(response)
        else:
            serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create term and conditions."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        terms_updated = serializer.save()
        data = TermAndConditionsModelSerializer(terms_updated, many=True).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, url_path='digital-dni', methods=['post', 'get'])
    def digital_dni(self, request, *args, **kwargs):
        """Digital dni login."""
        if request._request.method == 'GET':
            queryset = self.filter_queryset(self.get_queryset())
            if not queryset:
                # Empty terms from db
                term = self.terms.filter(is_principal=False)
                response = self.empty_response(term)
                return Response(response)
            serializer = TermAndConditionsModelSerializer(queryset)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            term = serializer.save()
            data = TermAndConditionsModelSerializer(term).data
            return Response(data, status=status.HTTP_201_CREATED)
