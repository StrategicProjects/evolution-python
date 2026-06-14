"""jid() helper and client configuration / validation."""

from __future__ import annotations

import pytest

from evolution_api import EvoClient, jid
from evolution_api._http import USER_AGENT
from evolution_api.exceptions import EvolutionConfigError


def test_jid_strips_non_digits_including_plus() -> None:
    assert jid("+55 81 99999-0000") == "5581999990000@s.whatsapp.net"
    assert jid("5581999990000") == "5581999990000@s.whatsapp.net"
    assert jid("(81) 99999.0000") == "81999990000@s.whatsapp.net"


def test_jid_vectorized() -> None:
    assert jid(["+5581999990000", "5511988887777"]) == [
        "5581999990000@s.whatsapp.net",
        "5511988887777@s.whatsapp.net",
    ]


def test_client_strips_trailing_slash_and_sets_headers() -> None:
    c = EvoClient("https://host/", "k", "inst")
    assert c.base_url == "https://host"
    headers = c._headers
    assert headers["apikey"] == "k"
    assert headers["Content-Type"] == "application/json"
    assert headers["User-Agent"] == USER_AGENT
    assert "evolution-api-python" in USER_AGENT


def test_client_repr() -> None:
    assert repr(EvoClient("https://host", "k", "inst")) == (
        "EvoClient(base_url='https://host', instance='inst')"
    )


@pytest.mark.parametrize(
    ("base_url", "api_key", "instance"),
    [
        ("", "k", "i"),
        ("https://h", "", "i"),
        ("https://h", "k", ""),
    ],
)
def test_client_rejects_empty_config(base_url: str, api_key: str, instance: str) -> None:
    with pytest.raises(EvolutionConfigError):
        EvoClient(base_url, api_key, instance)


def test_api_key_and_instance_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVO_APIKEY", "env-key")
    monkeypatch.setenv("EVO_INSTANCE", "env-inst")
    c = EvoClient("https://host")
    assert c.api_key == "env-key"
    assert c.instance == "env-inst"


def test_timeout_default_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EVOLUTION_TIMEOUT", raising=False)
    assert EvoClient("https://host", "k", "i").timeout == 60.0
    monkeypatch.setenv("EVOLUTION_TIMEOUT", "12.5")
    assert EvoClient("https://host", "k", "i").timeout == 12.5
    # Explicit arg wins over env.
    assert EvoClient("https://host", "k", "i", timeout=5).timeout == 5.0


def test_invalid_env_timeout_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVOLUTION_TIMEOUT", "not-a-number")
    with pytest.raises(EvolutionConfigError):
        EvoClient("https://host", "k", "i")
