import datetime
import json
import os

from django.conf import settings
from django.urls import reverse

from main.models import Notifications, UploadNotifications as UpNotifs, Parameter


def custom_context_data(request):
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

    # Get parameter queryset from db
    parameters = Parameter.objects

    if request.user.is_authenticated:
        current_url = request.path

        # Listing all guidelines for Profile
        if parameters.exists():
            p: Parameter = parameters.first()

            profile_create_url = reverse("main:profile-create")
            profile_edit_url = reverse("main:profile-edit", kwargs={"pk": 1})
            profile_edit_url = profile_edit_url.split('/')[:-2]
            profile_edit_url = profile_edit_url + ['']
            profile_edit_url = '/'.join(profile_edit_url)

            if current_url == profile_create_url or profile_edit_url in current_url:
                key = 'profile-guidelines'
                param = json.loads(p.parameter)
                profile_guideline = param[key] if key in param.keys() else []

                default_context['guidelines'] = profile_guideline

        # Guidelines for sfdcDigest node generator
        digest_url = reverse("main:digest-generator")
        if current_url == digest_url:
            guidelines = [
                {
                    "icon": "fa-lightbulb",
                    "text": "<strong>#1. </strong>You can specify multiple salesforce objects separated by a comma "
                            "(<code><strong>,</strong></code>).<br/><br/>"
                            "<strong>#2. </strong>To group fields by objects (in the order specified at "
                            "<code>SF Object API Name</code>, use a new line with <code><strong>--</strong></code> double "
                            "hyphen. For example: "
                            "<br/><code>Field A<br/>Field B<br/><strong>--</strong><br/>Field C<br/>Field D</code>",
                    "color": "success",
                    "title": "Tips"
                }
            ]
            default_context['guidelines'] = default_context['guidelines'] + guidelines \
                if 'guidelines' in default_context.keys() else guidelines

        # Guidelines for node extractor
        extract_url = reverse("main:extract-by-action")
        if current_url == extract_url:
            guidelines = [
                {
                    "icon": "fa-question",
                    "text": "You can use this extractor to generate a partial dataflow with only digest nodes and test "
                            "it quickly in org62. For example, extract only the <code>sfdcDigest</code> nodes from a "
                            "dataflow and run it in <strong><code>Wave Operation Support</code></strong> dataflow in "
                            "org62 and check for the correct field access.",
                    "color": "primary",
                    "title": "When to use it?"
                },
                {
                    "icon": "fa-lightbulb",
                    "text": "<ol><li>Select a dataflow.</li><li>Select a node action type. Ex: <code>sfdcDigest</code>."
                            "</li><li>Hit the button <strong><code>Get</code></strong>.</li></ol>",
                    "color": "success",
                    "title": "How to use"
                }
            ]
            default_context['guidelines'] = default_context['guidelines'] + guidelines \
                if 'guidelines' in default_context.keys() else guidelines

    # Flag to show alert banner for Stage env.
    heroku_app_env = os.environ.get('HEROKU_APP_ENV', "non-production")
    default_context['heroku_app_env'] = heroku_app_env.lower()

    # Custom title for the app
    site_name = "BT DNA"
    if parameters.exists():
        param = json.loads(parameters.first().parameter)

        if 'site-name' in param.keys():
            site_name = param['site-name']
    default_context['site_name'] = site_name

    # Version of the product
    default_context['version'] = settings.APP_VERSION_NUMBER

    return default_context
