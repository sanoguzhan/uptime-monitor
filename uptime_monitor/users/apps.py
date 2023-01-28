from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "uptime_monitor.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import uptime_monitor.users.signals  # noqa F401
        except ImportError:
            pass
