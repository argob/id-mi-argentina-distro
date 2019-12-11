# coding=utf-8
import time
import logging
import requests
from django.conf import settings
from requests.auth import AuthBase

logger = logging.getLogger("custom_info")

class JWT(object):
    """Representación del JSON Web Token."""

    token = None
    expires_in = None
    time_asked = None

    def __init__(self, *args, **kwargs):
        """Crea una nueva instancia de JWT, seteando el token."""
        self._set_token()
        super(JWT, self).__init__(*args, **kwargs)

    @classmethod
    def _set_token(cls):
        """Metodo de clase, que setea el token a la misma, para que todas las instancias tengan el mismo."""
        time_now = time.time()
        if cls.token is None or (time_now - cls.time_asked > cls.expires_in):
            credentials = {"username": settings.API_GATEWAY_USER, "password": settings.API_GATEWAY_PASSWORD}
            logger.info("JWT - Requesting access_token.")
            cls.time_asked = time.time()
            r = requests.post(settings.API_GATEWAY_AUTH_URL, data=credentials, timeout=10)
            if r.status_code == 200:
                json_response = r.json()
                cls.token = json_response['token']
                cls.expires_in = json_response['expires_in']
                logger.info("JWT - Access Granted.")
            else:
                logger.error("JWT - Access Denied.")
class JWTAuth(AuthBase):
    """Un sistema de Autorización/Autenticación para la librería 'requests', implementando JSON Web Token."""

    def __init__(self, alg='HS256', header_format='Bearer %s'):
        """Crea una nueva instancia de JWTAuth, seteando el token JWT."""
        jwt = JWT()
        self.secret = jwt.token
        self.alg = alg
        self._header_format = header_format

    def __call__(self, request):
        """
        Invocado por la librería 'requests' cuando se hace un request, agrega el header 'Authorization' al request.
        """
        request.headers['Authorization'] = self._header_format % self.secret
        return request

    @classmethod
    def refresh_jwt(self):
        JWT.token = None