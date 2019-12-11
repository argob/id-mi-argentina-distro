from __future__ import absolute_import, unicode_literals
import os

from celery import Celery

from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'id.settings')

celery_app = Celery("id")

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

celery_app.conf.update({
    'beat_schedule': {

    }})
# Load task modules from all registered Django app configs.
celery_app.autodiscover_tasks()
