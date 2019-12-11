# -*- coding: utf-8 -*-
from django.conf import settings
from requests import post


def verify_response(response):
    """
    Verifying the user's response.
    Read more: https://developers.google.com/recaptcha/docs/verify
    """
    data = {
        'secret': settings.RECAPTCHA_SECRET,
        'response': response,
    }
    r = post('https://www.google.com/recaptcha/api/siteverify', data=data, timeout=None)
    return r.json().get('success', False)
