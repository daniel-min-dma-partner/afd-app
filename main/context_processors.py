import datetime
from django.urls import reverse

from main.models import Notifications, UploadNotifications as UpNotifs


def show_notifications(request):
    lst = Notifications.objects.filter(user_id=request.user.pk).order_by('status', '-created_at')
    up_notifs = UpNotifs.objects.filter(user_id=request.user.pk).order_by('status', '-created_at')
    up_notif_ids = [n.id for n in up_notifs]

    ### Information ###
    # If you use `user=request.user` and you are not logged in, then it will throws an exception.
    # The reason is that the user object of the request object is not iterable when it is an anonymous.
    # Use `user_id=request.user.pk`

    default_context = {
        'notifications': [n for n in lst.all() if n.id not in up_notif_ids],
        'upload_notifications': up_notifs.all(),
        'currentYear': datetime.datetime.now().strftime("%Y")
    }

    profile_create_url = reverse("main:profile-create")
    profile_edit_url = reverse("main:profile-edit", kwargs={"pk": 1})
    profile_edit_url = profile_edit_url.split('/')[:-2]
    profile_edit_url = profile_edit_url + ['']
    profile_edit_url = '/'.join(profile_edit_url)
    current_url = request.path

    if current_url in [profile_create_url, profile_edit_url]:
        profile_guideline = [
            {
                "title": "Timezone",
                "text": """You can setup your custom timezone, specifying the key as <code><strong>timezone</strong></code>
                           and the value as one of the valid timezone strings which you can find
                           <a href="https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568#file-pytz-time-zones-py"
                           target="_blank">here</a>.""",
                "color": "success",
                "icon": "fa-globe-americas"
            },
            {
                "title": "A",
                "text":"B",
                "color":"warning",
                "icon": "fa-galactic-senate"
            }
        ]
        default_context['profile_guidelines'] = profile_guideline

    return default_context
