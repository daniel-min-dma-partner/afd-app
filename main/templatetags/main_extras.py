import os.path

from django import template
from django.template.defaultfilters import stringfilter

from main.models import Notifications

register = template.Library()


@register.filter
@stringfilter
def remove_prefix(value):
    return value.replace("ORIGINAL__", "").replace('DEPRECATED__', '')


@register.filter
def only_unreads(notifications: list):
    return [notification for notification in notifications if
            isinstance(notification, Notifications) and notification.status != 3]


@register.filter
def basename(path: str):
    return os.path.basename(path.split(" ")[-1])


@register.filter
def parse_to_color(string: str):
    string = string.lower()
    return 'danger' if string in ['error', 'err', 'errors'] else (
        'success' if string in ['ok', 'good', ] else string
    )
