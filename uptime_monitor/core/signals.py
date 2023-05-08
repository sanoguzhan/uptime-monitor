import json
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
import logging
from uptime_monitor.core.models import ScheduleItem

from django_celery_beat.models import  PeriodicTask

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ScheduleItem)
def create_scheduled_job(sender, instance, created, **kwargs):
    """
    Creates a scheduled job for a new monitor.
    """
    if instance.schedule is None:
        return
    if created:
        instance.periodic_task = PeriodicTask.objects.create(
            interval=instance.schedule,
            name=f"monitor_site_{instance.id}",
            task="check_site",
            kwargs=json.dumps({"check_registry_id": instance.check_registry.id}),
        )
        logger.info("Created scheduled job for monitor %s", instance.id)
        instance.save()
        
@receiver(pre_delete, sender=ScheduleItem)
def delete_scheduled_job(sender, instance, **kwargs):
    instance.periodic_task.delete()
    logger.info("Deleted scheduled job for monitor %s", instance.id)