from main.models import Notifications, UploadNotifications as UpNotifs


def show_notifications(request):
    lst = Notifications.objects.filter(user_id=request.user.pk).order_by('status', '-created_at')
    up_notifs = UpNotifs.objects.filter(user_id=request.user.pk).order_by('status', '-created_at')

    ### Information ###
    # If you use `user=request.user` and you are not logged in, then it will throws an exception.
    # The reason is that the user object of the request object is not iterable when it is an anonymous.
    # Use `user_id=request.user.pk`

    return {
        'notifications': lst.all(),
        'upload_notifications': up_notifs.all()
    }
