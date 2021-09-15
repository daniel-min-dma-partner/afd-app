import datetime
import json
import os

from django.urls import reverse
from django.utils.safestring import mark_safe

from main.models import Notifications, UploadNotifications as UpNotifs, Parameter


def show_notifications(request):
    # Get parameter queryset from db
    parameters = Parameter.objects

    # Listing all notifications
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

    # Listing all guidelines for Profile
    if request.user.is_authenticated:
        if parameters.exists():
            p: Parameter = parameters.first()

            profile_create_url = reverse("main:profile-create")
            profile_edit_url = reverse("main:profile-edit", kwargs={"pk": 1})
            profile_edit_url = profile_edit_url.split('/')[:-2]
            profile_edit_url = profile_edit_url + ['']
            profile_edit_url = '/'.join(profile_edit_url)
            current_url = request.path

            if current_url == profile_create_url or profile_edit_url in current_url:
                key = 'profile-guidelines'
                param = json.loads(p.parameter)
                profile_guideline = param[key] if key in param.keys() else []

                default_context['profile_guidelines'] = profile_guideline

    # Flag to show alert banner for Stage env.
    heroku_app_env = os.environ.get('HEROKU_APP_ENV', "")
    default_context['heroku_app_env'] = heroku_app_env.lower()

    # Custom title for the app
    site_name = "BT DNA"
    if parameters.exists():
        param = json.loads(parameters.first().parameter)

        if 'site-name' in param.keys():
            site_name = param['site-name']

    default_context['site_name'] = site_name

    return default_context
