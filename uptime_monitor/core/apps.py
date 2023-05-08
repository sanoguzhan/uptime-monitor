from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'uptime_monitor.core'

    def ready(self) -> None:
        from uptime_monitor.core.producer import check_site
        from uptime_monitor.core.consumer import save_response_history
        from uptime_monitor.core import signals