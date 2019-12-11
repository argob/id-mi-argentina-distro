import base64
import json
import os

from django.contrib.auth import logout, REDIRECT_FIELD_NAME
from django.contrib.sessions.models import Session
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.views.generic import View
from oidc_provider.lib.utils.oauth2 import protected_resource_view

from id.models import Locality, District


class LocalitiesApiView(View):
    def get(self, request, *args, **kwargs):
        state = request.GET.get('state', '')

        response = {'success': True, 'results': []}

        cached_results = cache.get('localities_' + state.lower())
        if cached_results:
            response['results'] = cached_results
        else:
            for locality in Locality.objects.filter(
                    state=state.upper()).order_by('name'):
                response['results'].append({
                    'name': locality.name, 'value': str(locality.id)
                })

            cache.set(
                'localities_' + state.lower(),
                response['results'], 2592000
            )  # 30 days.

        return JsonResponse(response)


@cache_page(24 * 60 * 60)
def districts_api(request):
    province_id = request.GET.get("province", None)

    results = []

    if province_id:
        districts = District.objects.filter(province_id=province_id).order_by('name')
        results = [{'name': district.name, 'value': district.id} for district in districts]

    response = {'success': True, 'results': results}
    return JsonResponse(response)
