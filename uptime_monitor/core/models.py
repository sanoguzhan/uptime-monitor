from django.db import models
import croniter
from http import HTTPStatus
from http import HTTPMethod
from typing import List, Tuple
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

HTTP_STATUS_CHOICES: List[Tuple[int, str]] = [(s.value, s.name) for s in HTTPStatus]
class SiteCheckStatus(models.TextChoices):
    PASS = "PASS", _("Response status is matched with the check registry status code.")
    FAIL = "FAIL", _("Response status is not matched with the check registry status code.")
    MISMATCH = "MISMATCH", _("Text is not matched.")
    TIMEOUT = "TIMEOUT", _("Request timeout.")
    ERROR = "ERROR", _("Request failed with an error.")
    
class SiteRegistry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    url = models.URLField(max_length=200)
    status_code = models.IntegerField(
        choices=HTTP_STATUS_CHOICES, default=HTTPStatus.OK.value
    )
    http_method = models.CharField(
        choices=[(s.value, s.name) for s in HTTPMethod],
        default=HTTPMethod.GET.value,
        max_length=10,
    )
    text = models.CharField(max_length=128, null=True, blank=True)
    hosted_at = models.CharField(max_length=128, null=True, blank=True)
    timeout = models.IntegerField(default=5)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self) -> str:
        return self.url


class SiteResponseHistory(models.Model):
    check_registry = models.ForeignKey(SiteRegistry, on_delete=models.CASCADE, related_name="history")
    response_code = models.CharField(
        choices=SiteCheckStatus.choices,  max_length=10
    )
    response_text = models.CharField(max_length=256, null=True, blank=True)
    response_time = models.FloatField()
    response_headers = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return "{} - {}".format(self.check_registry.url, self.response_code)

class ScheduleItem(models.Model):
    name = models.CharField(max_length=64, unique=True)
    check_registry = models.ForeignKey(SiteRegistry, on_delete=models.CASCADE, related_name="schedules")
    schedule = models.CharField(max_length=64, default="* * * * *")

    def save(self, *args, **kwargs):
        if not croniter.is_valid(self.schedule):
            raise Exception('"{}" is not a valid Cron schedule'.format(self.schedule))
        else:
            super(ScheduleItem, self).save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["check_registry"]),
        ]

    def __str__(self) -> str:
        return "{} - {}".format(self.name, self.schedule)