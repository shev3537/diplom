from django.apps import AppConfig

class DocsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'  # Должно совпадать с именем в INSTALLED_APPS