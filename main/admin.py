from django.contrib import admin
from django.db.models import JSONField
from jsoneditor.forms import JSONEditor

# Register your models here.
from .models import SalesforceEnvironment, Parameter


@admin.register(SalesforceEnvironment)
class SalesforceEnvironmentAdmin(admin.ModelAdmin):
    list_display = ("name", "environment", "user")


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': JSONEditor},
    }
