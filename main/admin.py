from django.contrib import admin

# Register your models here.
from .models import SalesforceEnvironment


@admin.register(SalesforceEnvironment)
class SalesforceEnvironmentAdmin(admin.ModelAdmin):
    list_display = ("name", "environment", "user")
