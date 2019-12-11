try:
    from django.utils import simplejson
except:
    import json as simplejson

# Django
from django.conf import settings
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login


def json_response(func):
    """
    A decorator thats takes a view response and turns it
    into json. If a callback is added through GET or POST
    the response is JSONP.
    """
    def decorator(request, *args, **kwargs):
        objects = func(request, *args, **kwargs)

        if type(objects) is HttpResponse:
            return objects

        try:
            data = simplejson.dumps(objects, cls=DjangoJSONEncoder)
            if 'callback' in request.GET:
                # a jsonp response!
                data = '%s(%s);' % (request.GET.get('callback', ''), data)
                return HttpResponse(data, content_type="application/javascript")
        except Exception as e:
            data = simplejson.dumps(str(objects), cls=DjangoJSONEncoder)

        return HttpResponse(data, content_type="application/json")
    return decorator


def group_required(*group_names):
    """
    Requires user membership in at least one of the groups passed in.
    """
    def wrap(view):
        def wrapped_view(request, *args, **kwargs):
            user = request.user
            if user.is_authenticated:
                check_groups = bool(user.groups.filter(name__in=group_names)) \
                    if group_names else True
                if user.is_superuser and check_groups:
                    return view(request, *args, **kwargs)
                else:
                    return render(request, 'admin/access_denied.html')
            else:
                path = request.get_full_path()
                return redirect_to_login(
                    path, settings.LOGIN_URL, REDIRECT_FIELD_NAME)
        return wrapped_view
    return wrap
