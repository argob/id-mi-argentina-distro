# -*- coding: utf-8 -*-
"""
Decoradores de cuenta
"""
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.utils.translation import ugettext as _


def login_required(view):
    """
    Ensure the user is logged in.
    """
    def view_wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view(request, *args, **kwargs)
        else:
            if request.is_ajax():
                return JsonResponse({'error': _(u'Debes estar logueado.')}, status=400)
            else:
                path = request.get_full_path()
                return redirect_to_login(path)
    return view_wrapper
