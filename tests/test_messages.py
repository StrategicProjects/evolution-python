"""Every send_* method: endpoint path, request body, compaction, warnings."""

from __future__ import annotations

import base64

import pytest
import respx

from evolution_api import EvoClient

from .conftest import BASE_URL, INSTANCE, last_body, ok


def url(endpoint: str) -> str:
    return f"{BASE_URL}/message/{endpoint}/{INSTANCE}"


def test_send_text_minimal_body_is_compacted(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendText")).mock(return_value=ok())
    client.send_text("5581999990000", "Hi")
    assert route.called
    # Optional None args are dropped (port of R .compact()).
    assert last_body(route) == {"number": "5581999990000", "text": "Hi"}


def test_send_text_full_body_camelcase(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendText")).mock(return_value=ok())
    client.send_text(
        "5581999990000",
        "Hi",
        delay=120,
        link_preview=False,
        mentions_everyone=True,
        mentioned=["x@s.whatsapp.net"],
        quoted={"key": {"id": "A"}},
    )
    body = last_body(route)
    assert body["delay"] == 120
    assert body["linkPreview"] is False
    assert body["mentionsEveryOne"] is True
    assert body["mentioned"] == ["x@s.whatsapp.net"]
    assert body["quoted"] == {"key": {"id": "A"}}


def test_send_text_returns_parsed_json(client: EvoClient, respx_mock: respx.Router) -> None:
    respx_mock.post(url("sendText")).mock(
        return_value=ok({"key": {"id": "BAE5"}, "status": "PENDING"})
    )
    result = client.send_text("5581999990000", "Hi")
    assert result["key"]["id"] == "BAE5"
    assert result["status"] == "PENDING"


def test_send_status(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendStatus")).mock(return_value=ok())
    client.send_status("text", "Hello", background_color="#317873", font=2, all_contacts=True)
    body = last_body(route)
    assert body["type"] == "text"
    assert body["backgroundColor"] == "#317873"
    assert body["allContacts"] is True


def test_send_status_invalid_type(client: EvoClient) -> None:
    with pytest.raises(Exception, match="type must be one of"):
        client.send_status("gif", "x")  # type: ignore[arg-type]


def test_send_media_url(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendMedia")).mock(return_value=ok())
    client.send_media(
        "5581999990000",
        "image",
        "image/png",
        "https://example.com/x.png",
        "x.png",
        caption="cap",
    )
    body = last_body(route)
    assert body["mediatype"] == "image"
    assert body["mimetype"] == "image/png"
    assert body["media"] == "https://example.com/x.png"
    assert body["fileName"] == "x.png"
    assert body["caption"] == "cap"


def test_send_media_local_file_base64(
    client: EvoClient, respx_mock: respx.Router, tmp_path
) -> None:
    f = tmp_path / "report.pdf"
    f.write_bytes(b"%PDF-1.4 test")
    route = respx_mock.post(url("sendMedia")).mock(return_value=ok())
    client.send_media("5581999990000", "document", "application/pdf", str(f), "report.pdf")
    assert last_body(route)["media"] == base64.b64encode(b"%PDF-1.4 test").decode()


def test_send_media_invalid_mediatype(client: EvoClient) -> None:
    with pytest.raises(Exception, match="mediatype must be one of"):
        client.send_media("5581999990000", "audio", "x", "https://x/y", "y")  # type: ignore[arg-type]


def test_send_whatsapp_audio(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendWhatsAppAudio")).mock(return_value=ok())
    client.send_whatsapp_audio("5581999990000", "https://example.com/a.ogg", delay=50)
    body = last_body(route)
    assert body == {"number": "5581999990000", "audio": "https://example.com/a.ogg", "delay": 50}


def test_send_sticker(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendSticker")).mock(return_value=ok())
    client.send_sticker("5581999990000", "https://example.com/s.webp")
    assert last_body(route)["sticker"] == "https://example.com/s.webp"


def test_send_location(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendLocation")).mock(return_value=ok())
    client.send_location("5581999990000", -8.05, -34.88, name="Recife", address="Marco Zero")
    body = last_body(route)
    assert body["latitude"] == -8.05
    assert body["longitude"] == -34.88
    assert body["name"] == "Recife"


def test_send_location_non_numeric(client: EvoClient) -> None:
    with pytest.raises(Exception, match="must be numeric"):
        client.send_location("5581999990000", "a", "b")  # type: ignore[arg-type]


def test_send_contact_single_auto_wuid(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendContact")).mock(return_value=ok())
    client.send_contact(
        "5581999990000",
        {"fullName": "Jane Doe", "phoneNumber": "+5581999990000"},
    )
    body = last_body(route)
    assert isinstance(body["contact"], list)
    assert body["contact"][0]["wuid"] == "5581999990000@s.whatsapp.net"
    assert body["contact"][0]["fullName"] == "Jane Doe"


def test_send_contact_multiple_and_falls_back_to_number(
    client: EvoClient, respx_mock: respx.Router
) -> None:
    route = respx_mock.post(url("sendContact")).mock(return_value=ok())
    client.send_contact(
        "5581999990000",
        [{"fullName": "No Phone"}, {"fullName": "Has Phone", "phoneNumber": "5511988887777"}],
    )
    contacts = last_body(route)["contact"]
    assert contacts[0]["wuid"] == "5581999990000@s.whatsapp.net"  # from `number`
    assert contacts[1]["wuid"] == "5511988887777@s.whatsapp.net"


def test_send_reaction(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendReaction")).mock(return_value=ok())
    key = {"remoteJid": "x@s.whatsapp.net", "fromMe": True, "id": "BAE5"}
    client.send_reaction(key, "\U0001f44d")
    assert last_body(route) == {"key": key, "reaction": "\U0001f44d"}


def test_send_reaction_requires_id(client: EvoClient) -> None:
    with pytest.raises(Exception, match="key must be a dict"):
        client.send_reaction({"remoteJid": "x"}, "\U0001f44d")


def test_send_poll(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendPoll")).mock(return_value=ok())
    client.send_poll("5581999990000", "Lang?", ["R", "Python", "Julia"], selectable_count=2)
    body = last_body(route)
    assert body["values"] == ["R", "Python", "Julia"]
    assert body["selectableCount"] == 2


def test_send_poll_needs_two_values(client: EvoClient) -> None:
    with pytest.raises(Exception, match="at least 2 options"):
        client.send_poll("5581999990000", "Q", ["only-one"])


def test_send_buttons_warns_baileys(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendButtons")).mock(return_value=ok())
    with pytest.warns(UserWarning, match="not supported on the Baileys"):
        client.send_buttons(
            "5581999990000",
            "Choose",
            "Pick:",
            "footer",
            [{"type": "reply", "title": "A"}],
        )
    assert route.called
    assert last_body(route)["footer"] == "footer"


def test_send_list_warns_and_defaults_footer(client: EvoClient, respx_mock: respx.Router) -> None:
    route = respx_mock.post(url("sendList")).mock(return_value=ok())
    with pytest.warns(UserWarning, match="not supported on the Baileys"):
        client.send_list(
            "5581999990000",
            "Menu",
            "Pick:",
            "View",
            [{"title": "Drinks", "rows": [{"title": "Coffee", "rowId": "1"}]}],
        )
    body = last_body(route)
    assert body["footerText"] == ""  # required by the API even when empty
    assert body["buttonText"] == "View"


def test_empty_number_rejected(client: EvoClient) -> None:
    with pytest.raises(Exception, match="number must be a single non-empty string"):
        client.send_text("", "hi")
