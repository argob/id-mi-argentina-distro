"""ID URls."""

# Django
from django.conf import settings
from django.urls import path, include
from django.conf.urls import url
from django.contrib import admin

# Project
from rest_framework.documentation import include_docs_urls


urlpatterns = [
    path('docs/', include_docs_urls(title='ID Api', public=False)),
    path('api/', include(('id.modules.api.urls', 'id'), namespace='api')),
    path('admin/', admin.site.urls),
    path('', include(('id.modules.accounts.urls', 'id'), namespace='accounts')),
    path('', include(('oidc_provider.urls'), namespace='oidc_provider')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
