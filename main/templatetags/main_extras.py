import os.path

from django import template
from typing import Union
from django.template.defaultfilters import stringfilter

from main.models import Notifications, UploadNotifications

register = template.Library()


@register.filter
@stringfilter
def remove_prefix(value):
    return value.replace("ORIGINAL__", "").replace('DEPRECATED__', '')


@register.filter
def only_unreads_up(notifications: list):
    return [notification for notification in notifications
            if isinstance(notification, UploadNotifications)
            and notification.status != 3]


@register.filter
def only_unreads(notifications: list):
    return [notification for notification in notifications
            if isinstance(notification, Notifications)
            and not UploadNotifications.objects.filter(notifications_ptr_id=notification.pk).exists()
            and notification.status != 3]


@register.filter
def basename(path: str):
    return os.path.basename(path.split(" ")[-1])


@register.filter
def parse_to_color(string: str):
    string = string.lower()
    return 'danger' if string in ['error', 'err', 'errors'] else (
        'success' if string in ['ok', 'good', ] else string
    )


@register.filter
def is_upload_notif(notification: Union[Notifications, UploadNotifications]):
    print('checking')
    return isinstance(notification, UploadNotifications)
