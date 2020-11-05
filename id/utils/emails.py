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
def send_email(to, subject, template_name, context=None, tags=None):
    html_content = render_to_string('emails/' + template_name, context if context else {})
    to = [to] if type(to) in [str] else to

    msg = EmailMessage(subject, html_content, settings.DEFAULT_FROM_EMAIL, to)
    msg.content_subtype = 'html'
    msg.tags = tags if tags else []

    msg.send(fail_silently=True)


def email_admins(subject, template_name, context=None):
    to = [e[1] for e in settings.ADMINS]
    send_email.delay(to, subject, template_name, context if context else {})

