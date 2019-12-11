"""Account URLs"""

# Django
from django.conf.urls import include
from django.urls import path

# Project
from id.modules.accounts.apis import (
    LocalitiesApiView, districts_api
)
from id.modules.accounts import views


urlpatterns = [
    path(
        route='',
        view=views.ProfileView.as_view(),
        name='home'
    ),
    path(
        route='ingresar/',
        view=views.UsersLoginView.as_view(),
        name='login'
    ),
    path(
        route='registro/',
        view=views.RegisterView.as_view(),
        name='register'
    ),
    path(
        route='registro/confirmar/<str:email>',
        view=views.ConfirmRegisterView.as_view(),
        name='confirm-registered-data'
    ),
    path(
        route='registro/success/<str:email>',
        view=views.SuccessRegisterView.as_view(),
        name='success-confirmation'
    ),
    path(
        route='terminos-condiciones/',
        view=views.TermsAndConditionsView.as_view(),
        name='terms-conditions'),

    path(
        route='activar-email/',
        view=views.EmailActivationView.as_view(),
        name='email-activation'
    ),
    path(
        route='activar-email/enviar/',
        view=views.SendEmailActivationView.as_view(),
        name='send-email-activation'
    ),
    path(
        route='salir/',
        view=views.UsersLogoutView.as_view(),
        name='logout'
    ),
    path(
        route='password/reset/',
        view=views.PasswordResetView.as_view(), name='password-reset'),
    path(
        route='password/set/',
        view=views.SetPasswordView.as_view(), name='password-set'),
    path(
        route='password/change/',
        view=views.PasswordChangeView.as_view(),
        name='password-change'),
    path(
        route='perfil/',
        view=views.ProfileView.as_view(),
        name='profile'
    ),
    path(
        route='configurar-mi-cuenta/',
        view=views.ProfileSettingsView.as_view(),
        name='profile-settings'
    ),
    path(
        route='eliminar/',
        view=views.DeleteView.as_view(),
        name='delete'
    ),
    path(
        route='api/', view=include([
            path(
                route='localities/',
                view=LocalitiesApiView.as_view(),
                name='localities'
            ),
            path(
                route='districts/',
                view=districts_api,
                name='districts'
            ),
        ])
    )
]
