from libs.interactor.interactor import Interactor
from main.models import Notifications, UploadNotifications


class SetNotificationInteractor(Interactor):
    def run(self):
        data = self.context.data
        klass = self.context.klass if 'klass' in self.context.__dict__.keys() else Notifications
        exception = None

        try:
            user = data['user']
            msg = data['message']
            link = data['link']
            status = data['status']
            type = data['type']

            notification = klass()
            notification.status = status
            notification.link = link
            notification.user = user
            notification.message = msg
            notification.type = type

            notification.save()

            if link == "__self__":
                notification.link = f'/notifications/view/{notification.pk}'
                notification.save()
            elif isinstance(notification, UploadNotifications):
                notification.link = link.replace("{{pk}}", str(notification.pk))
                notification.envname = data['envname']
                notification.zipfile_path = data['zipfile_path']
                notification.save()
        except Exception as e:
            exception = e
        finally:
            self.context.exception = exception
