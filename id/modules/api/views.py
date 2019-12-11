"""API Views"""

# Utils
import logging
import json
import warnings

# Django
from django.utils.decorators import method_decorator

# Django Rest Framework
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND
)
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView

# Project
from id.models import User
from oidc_provider.lib.utils.oauth2 import protected_resource_view
from id.authentication import BearerTokenAuthentication

logger = logging.getLogger()
