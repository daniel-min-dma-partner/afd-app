from django.contrib import admin
from django.db.models import JSONField
from jsoneditor.forms import JSONEditor

# Register your models here.
from .models import SalesforceEnvironment, Parameter, Job, JobStage


@admin.register(SalesforceEnvironment)
class SalesforceEnvironmentAdmin(admin.ModelAdmin):
    list_display = ("name", "environment", "user")


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': JSONEditor},
    }


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("message", "status", "progress", "user", "started_at", "finished_at")


@admin.register(JobStage)
class JobAdmin(admin.ModelAdmin):
    list_display = ("message", "status", "started_at", "finished_at")
