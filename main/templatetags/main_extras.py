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
            isinstance(notification, Notifications) and notification.status == 1]
