"""Accounts Views."""

# Utils
from datetime import datetime

# Django
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, authenticate,
    login as auth_login,
    logout as auth_logout
)
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import redirect, render, resolve_url
from django.utils.translation import ugettext as _
from django.views.generic import (
    View,
    FormView,
    TemplateView,
    UpdateView
)

# Sentry
from raven.contrib.django.raven_compat.models import client

# Django OIDC Provider
from oidc_provider.models import Token

# Forms
from id.forms import CustomSetPasswordForm, LoginForm
from id.modules.accounts.forms import (
    RegisterForm,
    UpdateProfileForm,
    PasswordResetForm,
    ChangePasswordForm,
    ConfirmRegisterForm,
    TermsAndConditionForms
)

# Project
from id.models import *
from id.utils.emails import send_email
from id.utils.validators import validate_date


class UsersLoginView(LoginView):
    """Login view custom based on auth views."""

    template_name = 'accounts/login.html'
    form_class = LoginForm
    http_method_names = ['get', 'post']

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirección incorrecta"
                )
            return HttpResponseRedirect(redirect_to)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Insert the next parameter into the context dict."""
        if 'next' not in kwargs:
            kwargs['next'] = self.request.POST.get(
                REDIRECT_FIELD_NAME, self.request.GET.get(REDIRECT_FIELD_NAME, ''))
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_redirect_url(self):
        """Return the user-originating redirect URL if it's safe."""

        redirect_to = self.request.POST.get(
            REDIRECT_FIELD_NAME,
            self.request.GET.get(REDIRECT_FIELD_NAME, '')
        )
        return redirect_to

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        user = form.get_user()
        auth_login(self.request, user)

        if not user.email_verified:
            return redirect(reverse('accounts:send-email-activation'))
        else:
            return redirect(self.get_success_url())

    def form_invalid(self, form):
        """Mostrar formulario de nuevo."""

        return super().form_invalid(form)


class UsersLogoutView(LoginRequiredMixin, LogoutView):
    """Logout view custom based on auth views"""
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            token = Token.objects.filter(user=request.user).last()
            token.expires_at = datetime.now()
            token.save()
        except:
            pass
        auth_logout(request)
        return redirect(
            request.GET.get(REDIRECT_FIELD_NAME, '') or reverse(
                settings.LOGIN_REDIRECT_URL)
        )


class RegisterView(FormView):
    """User Signup View."""
    template_name = 'accounts/register.html'
    template_name_confirmation = 'accounts/confirm_registered_data.html'
    form_class = RegisterForm
    second_form_class = TermsAndConditionForms

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        if 'countries' not in kwargs:
            kwargs['countries'] = Country.objects.order_by('name').all()
            kwargs['provinces'] = Province.objects.all()
            kwargs['districts'] = ''
            kwargs['localities'] = ''
            kwargs['terms_form'] = self.second_form_class()
            kwargs['next'] = self.request.GET.get(REDIRECT_FIELD_NAME, '')
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """

        form = self.get_form()
        form2 = self.second_form_class(request.POST)
        if form.is_valid():
            if form2.is_valid():
                email = form.cleaned_data['email']
                result_data = {**form.cleaned_data, **form2.cleaned_data}
                cache.set(
                    f'waiting_confirmation_{email}',
                    result_data, 60 * 123
                )

                return HttpResponseRedirect(
                    reverse_lazy(
                        'accounts:confirm-registered-data',
                        kwargs={'email': email}
                    )
                )
            return self.form_invalid(form2)
        return self.form_invalid(form)

    def form_invalid(self, form):
        """Retorno todos los errores"""
        return self.render_to_response(self.get_context_data(form=form))


class ConfirmRegisterView(TemplateView):
    """Confirm data registered"""
    template_name = 'accounts/confirm_registered_data.html'
    template_error = 'accounts/error_session.html'

    def dispatch(self, request, *args, **kwargs):
        """Verify that the data exist"""
        self.email = self.kwargs.get('email', None)
        self.data = cache.get(f'waiting_confirmation_{self.email}')
        if not self.data:
            return render(request, self.template_error)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Insert data into the context dict."""
        if 'data' not in kwargs:
            kwargs['data'] = self.data
        return super(ConfirmRegisterView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """Handle POST requests."""
        data = self.data
        terms = TermAndCondition.objects.all()
        terms_selected = {}
        for term in terms:
            slug = term.slug_name
            terms_selected[slug] = (term, data[slug])
            data.pop(slug)

        # Create and save the user and retrieve origin of data.
        user = User.create_id_user(data)
        if terms_selected:
            for user_term in terms_selected:
                user.usertermandcondition_set.create(
                    term=terms_selected[user_term][0],
                    is_active=terms_selected[user_term][1]
                )
        self.request.session['email_{}'.format(
            self.email)] = data.get('email')

        return HttpResponseRedirect(
            reverse_lazy(
                'accounts:success-confirmation',
                kwargs={'email': user.email})
        )


class TermsAndConditionsView(LoginRequiredMixin, FormView):
    """Terms and conditions"""
    template_name = 'accounts/termsandconditions.html'

    def dispatch(self, request, *args, **kwargs):
        """Dispatch method."""
        self.next = request.POST.get(
            REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME, False))
        self.terms = TermAndCondition.objects.filter(
            is_principal=True).order_by('id')

        if not request.user.is_anonymous:
            self.user_terms = self.request.user.usertermandcondition_set.filter(term__is_principal=True).order_by(
                'term',
                '-created')\
                .distinct('term')
        return super(TermsAndConditionsView, self).dispatch(request, *args, **kwargs)


    def get_form(self, form_class=None):
        """Returns an instance of the form to be used in this view."""
        if form_class is None:
            form_class = TermsAndConditionForms
        return form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        """return context to template with terms and conditions for
        current user.
        """
        kwargs['user_terms'] = self.request.user.usertermandcondition_set.all()
        return super(TermsAndConditionsView, self).get_context_data(**kwargs)

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
            'user': self.request.user,
            'user_terms': self.user_terms,
            'terms': self.terms,
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        data = form.cleaned_data
        # Update terms
        if self.user_terms:
            for term in form.changed_data:
                term_condition = self.terms.get(slug_name=term)
                user.usertermandcondition_set.create(
                    term=term_condition,
                    is_active=data[term]
                )
        else:
            # First selection of terms
            for term in data:
                try:
                    term_condition = self.terms.get(slug_name=term)
                except:
                    term_condition = TermAndCondition.objects.get(
                        slug_name=term)
                UserTermAndCondition.objects.create(
                    user=user,
                    term=term_condition,
                    is_active=data[term]
                )
        if self.next:
            return redirect(self.next)
        return super(TermsAndConditionsView, self).form_valid(form)

    def get_success_url(self):
        """Return to user's terms and conditions."""
        messages.success(
            self.request,
            'Tus términos y condiciones se actualizaron correctamente.'
        )
        return reverse_lazy('accounts:terms-conditions')


class SuccessRegisterView(TemplateView):
    """Success register view"""
    template_name = "accounts/success1.html"
    template_error = 'accounts/error_session.html'

    def get(self, request, *args, **kwargs):
        """Handle GET requests: read data from session"""
        context = self.get_context_data(**kwargs)
        email = self.request.session.get(
            'email_{}'.format(
                self.kwargs.get('email', None)
            ), None
        )

        if email:
            context['email'] = email
            return self.render_to_response(context)
        return render(request, self.template_error)


class EmailActivationView(View):

    def get(self, request, *args, **kwargs):
        try:
            token = EmailActivationToken.objects.only(
                'token', 'user_id', 'date_sent'
            ).get(token=request.GET.get('token'))

            if token.has_expired():
                raise EmailActivationToken.DoesNotExist
            User.objects.filter(id=token.user_id).update(
                email_verified=True
            )
            token.delete()
        except EmailActivationToken.DoesNotExist:
            messages.error(request, _(
                'El enlace de activación es incorrecto o ha expirado.'))

        return redirect(settings.MIAR_URL)


class SendEmailActivationView(LoginRequiredMixin, View):
    template_name = 'accounts/send_email_activation.html'

    def get(self, request, *args, **kwargs):
        if request.user.email_verified:
            return redirect(settings.MIAR_URL)
        else:
            kwargs['email'] = request.GET.get('email', '')
            return render(request, self.template_name, kwargs)

    def post(self, request, *args, **kwargs):
        try:
            request.user.resend_activation_email(
                next_url=kwargs[REDIRECT_FIELD_NAME])
        except:
            request.user.resend_activation_email(next_url='/')

        msg = _("El correo electrónico fue enviado a la cuenta <b>{0}</b><br />Por favor revisá tu casilla para "
                "completar el proceso.").format(
            request.user.email)
        messages.success(request, msg)
        return render(request, self.template_name, kwargs)


class PasswordResetView(FormView):
    """Reset password view"""
    template_email = 'accounts/password_reset_email.html'
    template_sent = 'accounts/password_reset_sent.html'
    template_change_password = 'accounts/password_reset_form.html'
    success_url = reverse_lazy('accounts:home')

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        token_exists = self.request.POST.get(
            'token', self.request.GET.get('token', ''))
        if token_exists:
            form_class = ChangePasswordForm
        else:
            form_class = PasswordResetForm
        return form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        kwargs['token'] = self.request.POST.get(
            'token', self.request.GET.get('token', ''))
        if 'form' not in kwargs:
            kwargs['form'] = self.get_form()
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        """If the form is valid, redirect to the supplied URL."""

        # Read form where comes the info to set redirection
        if isinstance(form, PasswordResetForm):
            return render(
                self.request,
                self.template_sent,
                context={'email': self.request.POST.get('email')}
            )

            messages.info(
                self.request, 'Tu contraseña se actualizó correctamente.')
            return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        # Check token expired error
        if isinstance(form, ChangePasswordForm):
            if form.errors.get('token'):
                messages.error(self.request, form.errors.get(
                    'token').data[0].message)
        return self.render_to_response(self.get_context_data(form=form))

    def render_to_response(self, context, **response_kwargs):
        """
        Return a response, using the `response_class` for this view, with a
        template rendered with the given context.
        Pass response_kwargs to the constructor of the response class.
        """
        response_kwargs.setdefault('content_type', self.content_type)
        if isinstance(context['form'], ChangePasswordForm):
            template = self.template_change_password

        else:
            template = self.template_email

        return self.response_class(
            request=self.request,
            template=template,
            context=context,
            using=self.template_engine,
            **response_kwargs)


class PasswordChangeView(LoginRequiredMixin, View):
    template_name = 'accounts/profile_settings.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('accounts:profile-settings'))

        return redirect(kwargs[REDIRECT_FIELD_NAME] or reverse(settings.LOGIN_REDIRECT_URL))

    def post(self, request, *args, **kwargs):
        data = {
            'password': request.POST.get('password', ''),
            'new_password': request.POST.get('new_password', ''),
            'new_password_again': request.POST.get('new_password_again', ''),
        }

        # Initialize field errors.
        errors = {key: False for (key, value) in data.items()}

        # Validate data.
        if not data['password']:
            errors['password'] = _('Falta ingresar este dato.')
        else:
            user = authenticate(
                username=request.user.username,
                password=data['password'])
            if not user:
                errors['password'] = _('La contraseña actual es incorrecta.')

        if not data['new_password']:
            errors['new_password'] = _('Falta ingresar este dato.')
        elif not len(data['new_password']) > 7:
            errors['new_password'] = _(
                'La nueva contraseña es demasiado corta.')

        if not data['new_password_again']:
            errors['new_password_again'] = _('Falta ingresar este dato.')
        elif not len(data['new_password']) > 7:
            errors['new_password'] = _(
                'La nueva contraseña es demasiado corta.')

        if not data['new_password'] == data['new_password_again']:
            errors['new_password'] = _('Las contraseñas no coinciden.')
            errors['new_password_again'] = _('Las contraseñas no coinciden.')

        # If not all of the keys are False.
        if not all([(not value) for (key, value) in errors.items()]):
            return JsonResponse({'errors': errors}, status=400)

        request.user.set_password(data['new_password'])
        request.user.save()

        return redirect('accounts:login')


class SetPasswordView(FormView):
    template_name = "accounts/password_set_form.html"
    form_class = CustomSetPasswordForm
    success_url = "/"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(
                request,
                "Cerrá sesión y vuelve acceder al link."
            )
            return redirect("/")

        return super(SetPasswordView, self).get(request, *args, **kwargs)

    def get_form(self, form_class=None):
        if self.request.method == "GET":
            # Validar que el token este activo
            try:
                token = PasswordResetToken.objects.get(
                    token=self.request.GET.get("token"))
            except PasswordResetToken.DoesNotExist:
                messages.info(self.request, _(
                    "El link ha expirado o ya ha sido utlizado"))
                raise Http404()

            return self.form_class(initial={"token": token.token})
        elif form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def form_valid(self, form):
        user = form.save()
        if user is None:
            messages.warning(self.request, _(
                "Ya has creado tu cuenta en MiArgentina"))
        else:
            messages.success(self.request, _(
                "Tu contraseña se creó con éxito. Inicia sesión"))

        return super(SetPasswordView, self).form_valid(form)

    def form_invalid(self, form):
        return super(SetPasswordView, self).form_invalid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    """Update user info"""

    template_name = 'accounts/profile.html'
    form_class = UpdateProfileForm
    success_url = reverse_lazy('accounts:home')

    def get_object(self):
        """return user profile"""
        return self.request.user

    def get_context_data(self, **kwargs):
        """Insert the form and other info into the context dict."""
        has_locality = self.request.user.locality
        province = self.request.user.locality.district.province if has_locality else None
        district_pk = self.request.user.locality.district.pk if has_locality else None
        locality_pk = self.request.user.locality.pk if has_locality else None

        if 'countries' and 'districts' and 'provinces' not in kwargs:
            kwargs['countries'] = Country.objects.order_by('name').all()
            kwargs['provinces'] = Province.objects.all()
            kwargs['districts'] = District.objects.filter(
                province=province
            ).exclude(pk=district_pk)
            kwargs['localities'] = Locality.objects.filter(
                district__pk=district_pk
            ).exclude(pk=locality_pk)
        return kwargs


    def get_form_kwargs(self):
        kwargs = super(ProfileView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """only storage the fields that had changes in form"""
        if form.changed_data:
            user = self.object
            user.save(update_fields=form.changed_data)
            if 'email' in form.changed_data:
                User.objects.filter(pk=self.object.pk).update(
                    email_verified=False)
                user.send_email_changed()
            messages.success(
                self.request, 'Tu perfil se actualizó correctamente.')
        return redirect(self.get_success_url())


class ProfileSettingsView(LoginRequiredMixin, View):
    template_name = 'accounts/profile_settings.html'

    def get(self, request, *args, **kwargs):
        kwargs['delete_reasons'] = ACCOUNT_DELETE_REASONS
        return render(request, self.template_name, kwargs)


class DeleteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('accounts:profile-settings'))

        return redirect(kwargs[REDIRECT_FIELD_NAME] or reverse(settings.LOGIN_REDIRECT_URL))

    def post(self, request, *args, **kwargs):
        reason = request.POST.get('reason', '')

        # Initialize field errors.
        errors = {}

        if not reason:
            errors['reason'] = _('Falta ingresar este dato.')

        # If not all of the keys are False.
        if not all([(not value) for (key, value) in errors.items()]):
            return JsonResponse({'errors': errors}, status=400)

        email = request.user.email
        request.user.delete()
        auth_logout(request)

        messages.warning(
            request,
            _('Borraste tu cuenta de Mi Argentina. Recordá que podés volver \
              a registrarte cuando quieras.')
        )

        send_email.delay(
            email,
            _(u'Borraste tu cuenta de Mi Argentina.'),
            'account_deleted.html',
            ['usuario-borra-cuenta',]
        )

        return JsonResponse({'deleted': True}, status=200)
