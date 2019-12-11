# -*- coding: utf-8 -*-

# Utilities
import requests
import logging

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# Celery
from celery import shared_task

logger = logging.getLogger()


@shared_task
def send_email(to, subject, template_name, context=None, tags=None, is_api=True):
    html_content = render_to_string('emails/' + template_name, context if context else {})
    to = [to] if type(to) in [str] else to

    if is_api:
        url = '{}/send/message'.format(settings.POSTAL['POSTAL_API_URL'])

        payload = {
            'to': to,
            'from': settings.POSTAL['POSTAL_FROM_EMAIL'],
            'subject': subject.encode('utf-8'),
            'html_body': html_content
        }

        if tags:
            payload['tag'] = tags

        header = {'X-Server-API-Key': settings.POSTAL['POSTAL_API_KEY']}
        response = requests.post(url, data=payload, headers=header)
        response_json = response.json()

        if response_json['status'] == 'error':
            logger.error(response_json)
    else:
        msg = EmailMessage(subject, html_content, settings.DEFAULT_FROM_EMAIL, to)
        msg.content_subtype = 'html'
        msg.tags = tags if tags else []

        msg.send(fail_silently=True)


def email_admins(subject, template_name, context=None):
    to = [e[1] for e in settings.ADMINS]
    send_email.delay(to, subject, template_name, context if context else {})

