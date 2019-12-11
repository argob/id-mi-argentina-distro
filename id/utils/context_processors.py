from django.conf import settings


def global_settings(request):
    """
    :param request: 
    :return: Any value of settings
    """

    return {
        'DEBUG': settings.DEBUG
    }
