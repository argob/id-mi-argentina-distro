"""Bearer authentication open ID"""

# Django
from django.contrib.auth import get_user_model

# Django Rest Framework
from rest_framework import authentication
from rest_framework import exceptions

# Oidc Provider
from oidc_provider.models import Token
from oidc_provider.lib.errors import BearerTokenError
from oidc_provider.lib.utils.oauth2 import extract_access_token

# Utils
import logging

logger = logging.getLogger(__name__)


class BearerTokenAuthentication(authentication.BaseAuthentication):
    """Bearer Token authentications"""
    def authenticate(self, request):
        access_token = extract_access_token(request)

        try:
            try:
                token = Token.objects.get(access_token=access_token)
            except Token.DoesNotExist:
                logger.debug('[UserInfo] Token does not exist: %s', access_token)
                return None

            if token.has_expired():
                logger.debug('[UserInfo] Token has expired: %s', access_token)
                return None

            if "openid" not in set(token.scope):
                logger.debug('[UserInfo] Missing openid scope.')
                return None
        except BearerTokenError as error:
            return None

        return (token.user, None)
