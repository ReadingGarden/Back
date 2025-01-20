from django.apps import AppConfig

from push.scheduler import PushScheduler


class PushConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'push'

    def ready(self):
        """
        앱이 준비될 때 호출되는 메서드입니다.
        스케줄러를 시작하고 종료 시 종료하도록 설정합니다.
        """
        from .scheduler import start_scheduler
        start_scheduler()
