"""API Urls."""

# Django
from django.conf.urls import include
from django.urls import path

# Rest Framework
from rest_framework import routers
from id.modules.api.accounts.views import (
    RegisterView, MeViewSet,
    CountryViewSet, ProvinceViewSet,
    DistrictViewSet, LocalityViewSet,
    PasswordResetView, LogoutViewView,
    LoginView, ActivationEmailView,
    TermAndConditionsViewset
)

# Views
from id.modules.api.accounts import views as accounts_views
from id.modules.api import views as id_views


router = routers.DefaultRouter()
router.register(r'country', accounts_views.CountryViewSet, basename='country')
router.register(r'province', accounts_views.ProvinceViewSet, basename='province')
router.register(r'district', accounts_views.DistrictViewSet, basename='district')
router.register(r'locality', accounts_views.LocalityViewSet, basename='locality')
router.register(r'me', accounts_views.MeViewSet, basename='me')
router.register(r'register', RegisterView, 'register')
router.register(r'terms-and-conditions', accounts_views.TermAndConditionsViewset, 'terms-and-conditions')


urlpatterns = [
    path(
        route='send-activation-email/',
        view=accounts_views.ActivationEmailView.as_view(),
        name='api-activation-email'
    ),
    path(
        route='v2/send-activation-email/',
        view=accounts_views.V2ActivationEmailView.as_view(),
        name='api-activation-email-v2'
    ),
    path(
        route='auth/logout/',
        view=accounts_views.LogoutViewView.as_view(),
        name='api-logout'),
    path(
        route='auth/password_reset/',
        view=accounts_views.PasswordResetView.as_view(),
        name='api-password-reset'),
    path(
        route='auth/v2/password_change/',
        view=accounts_views.PasswordChangeView.as_view(),
        name='api-password-change-v2'
    ),
    path(
        route='auth/',
        view=accounts_views.LoginView.as_view()
    ),
    path('', include(router.urls)),
]
