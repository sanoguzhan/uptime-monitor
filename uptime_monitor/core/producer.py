import datetime
import logging
from typing import Tuple
from config.celery_app import app
import httpx
from uptime_monitor.core.models import (
    SiteResponseStatus,
    SiteRegistry,
)
from uptime_monitor.core.consumer import save_response_history

logger = logging.getLogger(__name__)


def evaluate_response(
    response: httpx.Response,
    check_registry: SiteRegistry,
) -> Tuple[int, str]:
    """
    Evaluate the response from the request.
        if the response text is not matched with the check registry text, returns SiteResponseStatus.MISMATCH and response text.
        if the response status code is not matched with the check registry status code, returns SiteResponseStatus.FAIL and response text.
        otherwise, returns SiteResponseStatus.PASS and response text.

    Args:
        response: The response from the request.
        check_registry: The check registry to check.

    returns:
        A tuple of (SiteResponseStatus, response text).
    """
    if check_registry.text and check_registry.text.lower() not in response.text.lower():
        logger.error(
            "Site %s: Expected text: %s, got %s ",
            check_registry.url,
            check_registry.text,
            response.text,
        )
        return SiteResponseStatus.MISMATCH, response.text
    elif check_registry.status_code != response.status_code:
        logger.error(
            "Site %s: Expected status code: %s, got %s ",
            check_registry.url,
            check_registry.status_code,
            response.status_code,
        )
        return SiteResponseStatus.FAIL, response.text
    else:
        return SiteResponseStatus.PASS, response.text


@app.task(name="check_site", ignore_result=True)
def check_site(check_registry_id: int) -> None:
    """Check the status of a site.
        Evaluate the response from the request.
        Send the response to the save_response_history task on response_history queue.

    Args:
        check_registry: The check registry to check.
    """

    start = datetime.datetime.now()
    check_registry = SiteRegistry.objects.get(id=check_registry_id)
    logger.info("Sending request for %s", check_registry.url)
    http_method = check_registry.http_method.lower()
    status_code = None
    response_text = None

    with httpx.Client() as client:
        try:
            resp = getattr(client, http_method)(
                check_registry.url, timeout=check_registry.timeout
            )
            status_code = resp.status_code
        except httpx.TimeoutException as e:
            logger.exception("%s timeout.", check_registry.url)
            status_code = SiteResponseStatus.TIMEOUT
            response_text = str(e)
        except httpx.HTTPError as e:
            logger.exception("Error checking %s", check_registry.url)
            status_code = e.response.status_code
            response_text = str(e)
        else:
            status_code, response_text = evaluate_response(resp, check_registry)
            
    response_time_seconds: int = (datetime.datetime.now() - start).total_seconds()

    save_response_history.apply_async(
        kwargs={
            "data": {
                "check_registry": check_registry.id,
                "response_code": status_code,
                "response_text": response_text,
                "response_time": response_time_seconds,
                "response_headers": str(resp.headers),
            }
        },
        queue="response_history",
        ignore_result=True,
    )
