import json
from http import HTTPMethod, HTTPStatus
from typing import List, Tuple

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import IntervalSchedule, PeriodicTask

User = get_user_model()

HTTP_STATUS_CHOICES: List[Tuple[int, str]] = [(s.value, s.name) for s in HTTPStatus]


class SiteResponseStatus(models.TextChoices):
    PASS = "PASS", _("Response status is matched with the check registry status code.")
    FAIL = "FAIL", _(
        "Response status is not matched with the check registry status code."
    )
    MISMATCH = "MISMATCH", _("Text is not matched.")
    TIMEOUT = "TIMEOUT", _("Request timeout.")
    ERROR = "ERROR", _("Request failed with an error.")


class SiteRegistry(models.Model):
    """
    Model representing a site registry for monitoring website status.

    Attributes:
        user (ForeignKey): The user who created this site registry.
        created_at (DateTimeField): The date and time when this site registry was created.
        url (URLField): The URL of the website to be monitored.
        status_code (IntegerField): The HTTP status code to be checked against.
        http_method (CharField): The HTTP method to use for the request.
        text (CharField): The text to search for in the response body.
        hosted_at (CharField): The name of the hosting service for the website.
        timeout (IntegerField): The maximum time allowed for the request before timing out.
        last_checked_at (DateTimeField): The date and time when this site registry was last checked.
    """

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

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        """
        Returns the URL of the website being monitored as a string.
        """
        return self.url


class SiteResponseHistory(models.Model):
    """
    SiteResponseHistory representing a site response history for monitoring website status.

    Attributes:
        check_registry (ForeignKey): The site registry that this response history belongs to.
        response_code (CharField): The HTTP status code of the response.
        response_text (CharField): The text of the response.
        response_time (FloatField): The time taken to receive the response.
        response_headers (TextField): The headers of the response.
        created_at (DateTimeField): The date and time when this response history was created.
    """

    check_registry = models.ForeignKey(
        SiteRegistry, on_delete=models.CASCADE, related_name="history"
    )
    response_code = models.CharField(choices=SiteResponseStatus.choices, max_length=10)
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
    """
    ScheduleItem model representing a schedule item for monitoring website status.

    Attributes:
        name (CharField): The name of the schedule item.
        check_registry (ForeignKey): The site registry that this schedule item belongs to.
        schedule (ForeignKey): The schedule of the schedule item.
        periodic_task (ForeignKey): The periodic task of the schedule item.
    """

    PRODUCER_TASK_NAME = "check_site"

    name = models.CharField(max_length=64, unique=True)
    check_registry = models.ForeignKey(
        SiteRegistry, on_delete=models.CASCADE, related_name="schedules"
    )
    schedule = models.ForeignKey(IntervalSchedule, on_delete=models.PROTECT)
    periodic_task = models.ForeignKey(
        PeriodicTask, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["check_registry"]),
        ]

    def __str__(self) -> str:
        return "{} - {}".format(self.name, self.schedule)

    def save(self, *args, **kwargs):
        """
        Save the schedule item and create a periodic task if it does not exist.
        """

        try:
            self.periodic_task = PeriodicTask.objects.get(
                name=f"monitor_site_{self.name}"
            )
            self.periodic_task.interval = self.schedule
            self.periodic_task.save()
        except PeriodicTask.DoesNotExist:
            self.periodic_task = PeriodicTask.objects.create(
                name=f"monitor_site_{self.name}",
                task=self.PRODUCER_TASK_NAME,
                interval=self.schedule,
                kwargs=json.dumps({"check_registry_id": self.check_registry.id}),
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Delete the schedule item and the periodic task.
        """
        self.periodic_task.delete()
        super().delete(*args, **kwargs)
