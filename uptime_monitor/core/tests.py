import httpx
from unittest.mock import MagicMock
import pytest

from uptime_monitor.core.models import SiteResponseStatus, SiteRegistry
from uptime_monitor.core.producer import evaluate_response, check_site


@pytest.fixture
def site_registry_mock() -> SiteRegistry:
    """Fixture for a mock SiteRegistry object."""
    site_registry = MagicMock(spec=SiteRegistry)
    site_registry.id = 1234
    site_registry.url = "https://www.example.com"
    site_registry.http_method = "GET"
    site_registry.timeout = 5
    site_registry.text = "This is the Example Domain"
    site_registry.status_code = 200
    return site_registry


def test_evaluate_response_with_match_text_and_status_code(site_registry_mock) -> None:
    """Test evaluate_response function when response matches text and status code."""
    response = MagicMock(spec=httpx.Response)
    response.text = "This is the Example Domain"
    response.status_code = 200

    expected = (SiteResponseStatus.PASS, response.text)

    result = evaluate_response(response, site_registry_mock)

    assert result == expected


def test_evaluate_response_with_mismatched_text(site_registry_mock) -> None:
    """Test evaluate_response function when response has mismatched text."""
    response = MagicMock(spec=httpx.Response)
    response.text = "Random text."
    response.status_code = 200

    expected = (SiteResponseStatus.MISMATCH, response.text)

    result = evaluate_response(response, site_registry_mock)

    assert result == expected


def test_evaluate_response_with_mismatched_status_code(site_registry_mock) -> None:
    """Test evaluate_response function when response has mismatched status code."""
    response = MagicMock(spec=httpx.Response)
    response.text = "This is the Example Domain"
    response.status_code = 404

    expected = (SiteResponseStatus.FAIL, response.text)

    result = evaluate_response(response, site_registry_mock)

    assert result == expected


@pytest.mark.parametrize(
    "status_code,text,expected_result",
    [
        (200, "OK", SiteResponseStatus.PASS),
        (404, "Not Found", SiteResponseStatus.FAIL),
        (200, "Mismatch", SiteResponseStatus.MISMATCH),
        (500, "", SiteResponseStatus.FAIL),
    ],
)
def test_check_site(
    site_registry_mock: SiteRegistry,
    mocker: MagicMock,
    status_code: int,
    text: str,
    expected_result: SiteResponseStatus,
) -> None:
    """Test check_site function with different response parameters."""
    mocker.patch.object(SiteRegistry.objects, "get", return_value=site_registry_mock)
    httpx_client_mock = mocker.patch("httpx.Client")
    save_response_history_async_mock = mocker.patch(
        "uptime_monitor.core.consumer.save_response_history.apply_async"
    )

    httpx_response_mock = MagicMock(spec=httpx.Response)
    httpx_response_mock.status_code = status_code
    httpx_response_mock.text = text
    httpx_response_mock.headers = {"Content-Type": "text/html"}

    httpx_client_mock().__getitem__().get.return_value = httpx_response_mock

    check_site(site_registry_mock.id)

    save_response_history_async_mock.assert_called_once()
