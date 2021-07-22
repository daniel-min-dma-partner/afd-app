from main.models import Notifications


def show_notifications(request):
    lst = Notifications.objects.filter(user_id=request.user.pk).order_by('-created_at').all()
    return {'notifications': lst}
