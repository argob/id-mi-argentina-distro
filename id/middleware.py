# -*- encoding: utf-8 -*-

# Utils
import urllib
import urllib.parse
import json
from urllib.parse import urlparse, urlsplit, parse_qs

# Django
from django.contrib.auth import logout
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import ugettext as _


class EmailValidatedMiddleware:
    """Check if user has a validated email, if not, can only access to validation's URLs."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = [
            'email-activation',
            'send-email-activation',
            'logout',
            'profile'
        ]

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            has_terms = user.usertermandcondition_set.filter(term__is_principal=True)\
                .order_by(
                    'term',
                    '-created')\
                .distinct('term')

            if has_terms and not user.email_verified:
                if resolve(request.path).url_name not in self.whitelist:
                    return redirect('accounts:send-email-activation')

        response = self.get_response(request)

        return response


class TermsAndConditionsMiddleware:
    """Check if user has a terms and conditions enabled."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = ['terms-conditions', 'logout']

    def __call__(self, request):
        user = request.user
        if not user.is_anonymous:
            terms = user.usertermandcondition_set.filter(term__is_principal=True)\
                .order_by(
                    'term',
                    '-created')\
                .distinct('term')
            terms_count = terms.count()
            if terms_count < 3:
                # Some accounts have two or less terms and condition selected
                # and there will be cleaned to select three.
                if terms_count != 0:
                    terms.delete()

                if resolve(request.path).url_name not in self.whitelist:
                    return redirect('/terminos-condiciones/?next={}{}{}'.format(
                            request.path,
                            urllib.parse.quote('?', safe=''),
                            urllib.parse.quote(request.META['QUERY_STRING'], safe='')
                        )
                    )

        response = self.get_response(request)
        return response
