"""normalize_media() — URL passthrough, file→base64, data-URI, base64, errors."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from evolution_api.exceptions import EvolutionConfigError
from evolution_api.media import normalize_media


def test_http_url_passthrough() -> None:
    url = "https://example.com/img.png"
    assert normalize_media(url) == url
    assert normalize_media("HTTP://example.com/x") == "HTTP://example.com/x"


def test_local_file_is_base64_encoded(tmp_path: Path) -> None:
    f = tmp_path / "hello.bin"
    f.write_bytes(b"hello-bytes")
    assert normalize_media(str(f)) == base64.b64encode(b"hello-bytes").decode()


def test_tilde_expansion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    f = tmp_path / "note.ogg"
    f.write_bytes(b"audio")
    assert normalize_media("~/note.ogg") == base64.b64encode(b"audio").decode()


def test_data_uri_prefix_is_stripped() -> None:
    raw = base64.b64encode(b"abc").decode()
    assert normalize_media(f"data:image/png;base64,{raw}") == raw


def test_raw_base64_passthrough() -> None:
    raw = base64.b64encode(b"some content").decode()
    assert normalize_media(raw) == raw


def test_invalid_media_raises() -> None:
    with pytest.raises(EvolutionConfigError):
        normalize_media("not a url or file or base64 !!!")


def test_empty_media_raises() -> None:
    with pytest.raises(EvolutionConfigError):
        normalize_media("")
