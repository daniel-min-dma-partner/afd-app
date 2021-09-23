import json
import os.path
from typing import List
from typing import Union

from django import template
from django.template.defaultfilters import stringfilter

from main.models import Notifications, UploadNotifications, DeprecationDetails, Profile

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
    return isinstance(notification, UploadNotifications)


@register.filter
def is_deprecated(obj: DeprecationDetails):
    return obj.status == DeprecationDetails.SUCCESS


@register.filter
def deprecation_stats(lst: List[DeprecationDetails]):
    deprecated = no_deprecated = with_error = 0

    for obj in lst:
        deprecated += 1 if obj.status == DeprecationDetails.SUCCESS else 0
        no_deprecated += 1 if obj.status == DeprecationDetails.NO_DEPRECATION else 0
        with_error += 1 if obj.status == DeprecationDetails.ERROR else 0

    return f"{deprecated+no_deprecated+with_error} files: <code>{deprecated}</code> deprecated, <code>{no_deprecated}</code> no changes, <code>{with_error}</code> with errors."


@register.filter
@stringfilter
def profile_type_to_text(thype: str = ""):
    if not thype:
        return thype

    for item in Profile.TYPE_CHOICE_SELECT2:
        if item['id'] == thype:
            return item['text']

    return thype


@register.filter
def range_list(number: int):
    return range(number)


@register.filter
def index_of(value: list, arg):
    return value.index(arg) + 1


@register.filter
def get_status_badge(status: str):
    status_badges = {
        'created': "gray",
        'started': "primary",
        'progress': 'primary',
        'failed': 'danger',
        'success': 'success',
        'warning': 'warning',
    }

    return status_badges[status]


@register.filter
def json_safe(js: dict):
    return json.dumps(js, indent=2)
