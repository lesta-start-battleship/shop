from django.apps import AppConfig


class ChestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chest'

    # def ready(self):
    #     from apps.chest import signals
