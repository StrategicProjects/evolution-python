"""Transport behaviour: errors, retries, non-JSON, GET, verbose, check_numbers."""

from __future__ import annotations

import httpx
import pytest
import respx

from evolution_api import EvoClient
from evolution_api.exceptions import EvolutionAPIError, EvolutionConnectionError

from .conftest import BASE_URL, INSTANCE, ok


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make backoff instant so retry tests don't wait."""
    monkeypatch.setattr("evolution_api.client.time.sleep", lambda _s: None)


def test_error_surfaces_response_message(client: EvoClient, respx_mock: respx.Router) -> None:
    respx_mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
        return_value=httpx.Response(400, json={"response": {"message": ["number is required"]}})
    )
    with pytest.raises(EvolutionAPIError) as exc:
        client.send_text("5581999990000", "x")
    assert exc.value.status == 400
    assert exc.value.api_message == "number is required"
    assert exc.value.path == f"message/sendText/{INSTANCE}"


def test_error_falls_back_to_message_field(client: EvoClient, respx_mock: respx.Router) -> None:
    respx_mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    with pytest.raises(EvolutionAPIError, match="Unauthorized"):
        client.send_text("5581999990000", "x")


def test_non_json_error_does_not_crash(client: EvoClient, respx_mock: respx.Router) -> None:
    respx_mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
        return_value=httpx.Response(502, html="<html>Bad Gateway</html>")
    )
    with pytest.raises(EvolutionAPIError) as exc:
        client.send_text("5581999990000", "x")
    assert exc.value.status == 502
    assert "Bad Gateway" in exc.value.api_message


def test_retries_on_503_then_succeeds(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
        side_effect=[httpx.Response(503), httpx.Response(503), ok({"ok": True})]
    )
    result = client.send_text("5581999990000", "x")
    assert result == {"ok": True}
    assert route.call_count == 3


def test_gives_up_after_max_retries(respx_mock: respx.Router) -> None:
    client = EvoClient(BASE_URL, "k", INSTANCE, max_retries=2)
    route = respx_mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
        return_value=httpx.Response(503)
    )
    with pytest.raises(EvolutionAPIError) as exc:
        client.send_text("5581999990000", "x")
    assert exc.value.status == 503
    assert route.call_count == 2
    client.close()


def test_connection_error_raises_typed(client: EvoClient, respx_mock: respx.Router) -> None:
    respx_mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
        side_effect=httpx.ConnectError("boom")
    )
    with pytest.raises(EvolutionConnectionError, match="failed"):
        client.send_text("5581999990000", "x")


def test_connection_state_is_get(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.get(f"{BASE_URL}/instance/connectionState/{INSTANCE}").mock(
        return_value=httpx.Response(
            200, json={"instance": {"instanceName": INSTANCE, "state": "open"}}
        )
    )
    result = client.connection_state()
    assert route.called
    assert result["instance"]["state"] == "open"


def test_check_is_whatsapp_and_alias(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(f"{BASE_URL}/chat/whatsappNumbers/{INSTANCE}").mock(
        return_value=httpx.Response(200, json=[{"jid": "x", "exists": True}])
    )
    client.check_is_whatsapp(["5581999990000"])
    client.check_numbers(["5581999990000"])
    assert route.call_count == 2


def test_check_is_whatsapp_rejects_empty(client: EvoClient) -> None:
    with pytest.raises(Exception, match="non-empty list"):
        client.check_is_whatsapp([])


def test_apikey_header_sent(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(return_value=ok())
    client.send_text("5581999990000", "x")
    assert route.calls.last.request.headers["apikey"] == "test-key"
    assert "evolution-api-python" in route.calls.last.request.headers["user-agent"]


def test_verbose_logs(
    client: EvoClient, respx_mock: respx.Router, capfd: pytest.CaptureFixture[str]
) -> None:
    respx_mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(return_value=ok())
    client.send_text("5581999990000", "x", verbose=True)
    out, err = capfd.readouterr()
    combined = out + err
    assert "sendText" in combined
    assert "HTTP 201" in combined
