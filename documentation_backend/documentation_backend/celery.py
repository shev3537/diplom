# documentation_backend/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'documentation_backend.settings')

app = Celery('documentation_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
