from main.models import Notifications, UploadNotifications as UpNotifs


def show_notifications(request):
    lst = Notifications.objects.filter(user_id=request.user.pk).order_by('status', '-created_at')
    up_notifs = UpNotifs.objects.filter(user=request.user).order_by('status', '-created_at')

    return {
        'notifications': lst.all(),
        'upload_notifications': up_notifs.all()
    }
