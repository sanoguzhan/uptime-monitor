from typing import Dict
from config.celery_app import app

from uptime_monitor.core.serializers import SiteResponseHistorySerializer
from django.db import transaction

import logging

from uptime_monitor.core.models import SiteRegistry


logger = logging.getLogger(__name__)

@app.task(name="save_response_history", ignore_result=True)
def save_response_history(data: Dict[str,str]) -> None:
    """ Save the response history to the database.
        Updates the last_checked_at field of the SiteRegistry object.
    Args:
        data (Dict[str,str]): The data to save. Must be a valid SiteResponseHistorySerializer.
    """
    serializer = SiteResponseHistorySerializer(data=data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        instance = serializer.save()
        SiteRegistry.objects.filter(id=serializer.validated_data["check_registry"].id).update(
           last_checked_at = instance.created_at
        )
    logger.debug("Saved response history: %s", data)
    