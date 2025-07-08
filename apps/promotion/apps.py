from django.apps import AppConfig
from django.db.models.signals import post_migrate



class PromotionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.promotion'

    def ready(self):
        from .signals import create_periodic_task
        post_migrate.connect(create_periodic_task, sender=self)
        
            
