from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.db import OperationalError, ProgrammingError

def create_periodic_task(sender, **kwargs):
    try:
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone='Europe/Moscow'
        )

        if not PeriodicTask.objects.filter(name='Daily Promotion Compensation').exists():
            PeriodicTask.objects.create(
                crontab=schedule,
                name='Daily Promotion Compensation',
                task='apps.promotion.tasks.check_and_compensate_expired_promotions',
            )
    except (OperationalError, ProgrammingError):
        pass