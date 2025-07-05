from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
from django.db import connections

class PromotionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.promotion'

    def ready(self):
        try:
            connections['default'].cursor()
        except (OperationalError, ProgrammingError):
            return

        try:
            from django_celery_beat.models import PeriodicTask, CrontabSchedule

            if not PeriodicTask.objects.filter(name='Daily Promotion Compensation').exists():
                schedule, _ = CrontabSchedule.objects.get_or_create(
                    minute='0',
                    hour='0',
                    day_of_week='*',
                    day_of_month='*',
                    month_of_year='*',
                    timezone='Europe/Moscow'
                )

                PeriodicTask.objects.create(
                    crontab=schedule,
                    name='Daily Promotion Compensation',
                    task='apps.promotion.tasks.check_and_compensate_expired_promotions',
                )
        except (OperationalError, ProgrammingError):
            pass
