from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    pass

class CodeDocumentation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True, blank=True
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    code_example = models.TextField()
    pdf_file = models.FileField(upload_to='pdf_docs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class APIDocumentation(models.Model):
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    description = models.TextField()
    parameters = models.JSONField()
    responses = models.JSONField()

class DatabaseSchema(models.Model):
    name = models.CharField(max_length=100)
    schema = models.JSONField()
    description = models.TextField()