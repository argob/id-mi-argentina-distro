"""
Account mixins
"""
from django.contrib.auth import REDIRECT_FIELD_NAME

from braces.views._access import AccessMixin


class LoginRequiredMixin(AccessMixin):
    """
    View mixin which verifies that the user is authenticated.

    NOTE:
        This should be the left-most mixin of a view, except when
        combined with CsrfExemptMixin - which in that case should
        be the left-most mixin.
    """
    def dispatch(self, request, *args, **kwargs):
        kwargs['next'] = request.POST.get(REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME, ''))
        if not request.user.is_authenticated:
            return self.handle_no_permission(request)

        return super(LoginRequiredMixin, self).dispatch(
            request, *args, **kwargs)
