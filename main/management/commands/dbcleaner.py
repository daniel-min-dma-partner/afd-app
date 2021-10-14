from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from main.models import Job, Notifications


class Command(BaseCommand):
    help = 'Deletes all jobs last for more than 2 days.'

    def handle(self, *args, **options):
        self.stdout.write("\n")

        days = (datetime.utcnow()-timedelta(days=2)).astimezone()
        queries = [Job.objects.filter(started_at__lt=days).exclude(status__in=['created', 'started', 'progress']),
                   Notifications.objects.filter(created_at__lt=days, status__gte=3)]

        msg = f"Datetime {str(days)}"
        self.stdout.write(self.style.WARNING(msg))
        self.stdout.write("=" * len(msg))

        for query in queries:
            if query.exists():
                class_name = type(query.first()).__name__
                msg = f"{query.count()} {class_name} found. Ready to be removed."
                self.stdout.write(self.style.SUCCESS(msg))
                self.stdout.write(self.style.SUCCESS("=" * len(msg)))

                for model in query.all():
                    model.delete()
                    self.stdout.write(f"\t - {class_name} #{model.pk} {self.style.WARNING(model.message)} deleted.")
            else:
                self.stdout.write(self.style.SUCCESS(f"No {query.all().model.__name__} has been found."))

        self.stdout.write('\n')
