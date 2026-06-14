"""Message-sending methods — the ``send_*`` family, mirroring the R package.

Each method validates its arguments up front (port of the R
``.assert_scalar_string()`` checks), builds a compacted request body, and returns
``self._execute(spec)`` so the same definition serves the sync and async clients.
"""

from __future__ import annotations

import warnings
from typing import Any, Literal

from ._protocol import ClientCore
from ._spec import RequestSpec, compact, evo_path
from .exceptions import EvolutionConfigError
from .media import normalize_media
from .numbers import jid

__all__ = ["MessagesMixin"]

MediaType = Literal["image", "video", "document"]
StatusType = Literal["text", "image", "video", "document", "audio"]

_BAILEYS_WARNING = (
    "Interactive {kind} are not supported on the Baileys (WhatsApp Web) connector "
    "and may be discontinued; this endpoint works on the Cloud API connector only. "
    "Consider send_poll() as an alternative."
)


def _assert_scalar_string(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise EvolutionConfigError(f"{name} must be a single non-empty string.")


class MessagesMixin:
    """All ``send_*`` endpoints under ``message/<endpoint>/<instance>``."""

    def send_text(
        self: ClientCore,
        number: str,
        text: str,
        *,
        delay: int | None = None,
        link_preview: bool | None = None,
        mentions_everyone: bool | None = None,
        mentioned: list[str] | None = None,
        quoted: dict[str, Any] | None = None,
        verbose: bool | None = None,
    ) -> Any:
        """Send a plain text WhatsApp message.

        Args:
            number: Recipient with country code (``"5581999990000"`` or ``"+55..."``).
            text: Message body.
            delay: Optional presence delay in milliseconds (simulates typing).
            link_preview: Enable URL link preview.
            mentions_everyone: Mention everyone in a group.
            mentioned: JIDs to mention (e.g. ``jid("+5581999990000")``).
            quoted: Baileys message ``{"key": ..., "message": ...}`` to reply to.
            verbose: Override the client's verbose setting for this call.
        """
        _assert_scalar_string(number, "number")
        _assert_scalar_string(text, "text")
        body = compact(
            {
                "number": number,
                "text": text,
                "delay": delay,
                "linkPreview": link_preview,
                "mentionsEveryOne": mentions_everyone,
                "mentioned": mentioned,
                "quoted": quoted,
            }
        )
        spec = RequestSpec("POST", evo_path("message", "sendText", self.instance), body)
        return self._execute(spec, verbose=self._resolve_verbose(verbose))

    def send_status(
        self: ClientCore,
        type: StatusType,
        content: str,
        *,
        caption: str | None = None,
        background_color: str | None = None,
        font: int | None = None,
        all_contacts: bool = False,
        status_jid_list: list[str] | None = None,
        verbose: bool | None = None,
    ) -> Any:
        """Post a WhatsApp status (story): text or media.

        Args:
            type: One of ``"text"``, ``"image"``, ``"video"``, ``"document"``, ``"audio"``.
            content: Text (for ``type="text"``) or URL/base64 for media.
            caption: Optional caption for media types.
            background_color: Hex colour for a text status (e.g. ``"#FF5733"``).
            font: Integer font id (0-14).
            all_contacts: If ``True``, send to all contacts.
            status_jid_list: Specific JIDs to receive the status.
        """
        if type not in ("text", "image", "video", "document", "audio"):
            raise EvolutionConfigError(
                'type must be one of "text", "image", "video", "document", "audio".'
            )
        _assert_scalar_string(content, "content")
        body = compact(
            {
                "type": type,
                "content": content,
                "caption": caption,
                "backgroundColor": background_color,
                "font": font,
                "allContacts": bool(all_contacts),
                "statusJidList": status_jid_list,
            }
        )
        spec = RequestSpec("POST", evo_path("message", "sendStatus", self.instance), body)
        return self._execute(spec, verbose=self._resolve_verbose(verbose))

    def send_media(
        self: ClientCore,
        number: str,
        mediatype: MediaType,
        mimetype: str,
        media: str,
        file_name: str,
        *,
        caption: str | None = None,
        delay: int | None = None,
        link_preview: bool | None = None,
        verbose: bool | None = None,
    ) -> Any:
        """Send an image, video, or document.

        ``media`` is flexible: an HTTP(S) URL, a local file path (auto-encoded to
        base64, ``~`` expanded), raw base64, or a ``data:*;base64,`` URI.

        Args:
            number: Recipient with country code.
            mediatype: One of ``"image"``, ``"video"``, ``"document"``.
            mimetype: e.g. ``"image/png"``, ``"video/mp4"``, ``"application/pdf"``.
            media: URL, file path, base64, or data-URI.
            file_name: Suggested filename for the recipient (match the MIME type).
            caption: Optional caption displayed with the media.
        """
        _assert_scalar_string(number, "number")
        _assert_scalar_string(mimetype, "mimetype")
        _assert_scalar_string(file_name, "file_name")
        if mediatype not in ("image", "video", "document"):
            raise EvolutionConfigError(
                f'mediatype must be one of "image", "video", or "document". Got {mediatype!r}.'
            )
        resolved = self._resolve_verbose(verbose)
        body = compact(
            {
                "number": number,
                "mediatype": mediatype,
                "mimetype": mimetype,
                "caption": caption,
                "media": normalize_media(media, verbose=resolved),
                "fileName": file_name,
                "delay": delay,
                "linkPreview": link_preview,
            }
        )
        spec = RequestSpec("POST", evo_path("message", "sendMedia", self.instance), body)
        return self._execute(spec, verbose=resolved)

    def send_whatsapp_audio(
        self: ClientCore,
        number: str,
        audio: str,
        *,
        delay: int | None = None,
        quoted: dict[str, Any] | None = None,
        verbose: bool | None = None,
    ) -> Any:
        """Send a voice note (push-to-talk).

        ``audio`` accepts a URL, base64, or a local file path (``~`` expanded,
        auto-encoded to base64).
        """
        _assert_scalar_string(number, "number")
        _assert_scalar_string(audio, "audio")
        resolved = self._resolve_verbose(verbose)
        body = compact(
            {
                "number": number,
                "audio": normalize_media(audio, verbose=resolved),
                "delay": delay,
                "quoted": quoted,
            }
        )
        spec = RequestSpec("POST", evo_path("message", "sendWhatsAppAudio", self.instance), body)
        return self._execute(spec, verbose=resolved)

    def send_sticker(
        self: ClientCore,
        number: str,
        sticker: str,
        *,
        delay: int | None = None,
        verbose: bool | None = None,
    ) -> Any:
        """Send a sticker.

        ``sticker`` accepts a URL, base64, or a local file path (``~`` expanded,
        auto-encoded to base64).
        """
        _assert_scalar_string(number, "number")
        _assert_scalar_string(sticker, "sticker")
        resolved = self._resolve_verbose(verbose)
        body = compact(
            {
                "number": number,
                "sticker": normalize_media(sticker, verbose=resolved),
                "delay": delay,
            }
        )
        spec = RequestSpec("POST", evo_path("message", "sendSticker", self.instance), body)
        return self._execute(spec, verbose=resolved)

    def send_location(
        self: ClientCore,
        number: str,
        latitude: float,
        longitude: float,
        *,
        name: str | None = None,
        address: str | None = None,
        verbose: bool | None = None,
    ) -> Any:
        """Send a geographic location pin."""
        _assert_scalar_string(number, "number")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise EvolutionConfigError("latitude and longitude must be numeric values.")
        body = compact(
            {
                "number": number,
                "latitude": latitude,
                "longitude": longitude,
                "name": name,
                "address": address,
            }
        )
        spec = RequestSpec("POST", evo_path("message", "sendLocation", self.instance), body)
        return self._execute(spec, verbose=self._resolve_verbose(verbose))

    def send_contact(
        self: ClientCore,
        number: str,
        contact: dict[str, Any] | list[dict[str, Any]],
        *,
        verbose: bool | None = None,
    ) -> Any:
        """Send one or more contacts (the ``wuid`` field is auto-generated).

        Args:
            number: Recipient with country code.
            contact: A single contact dict (``fullName``, ``phoneNumber``,
                ``organization``, ``email``, ``url``) or a list of such dicts.
                ``wuid`` is generated as ``<digits>@s.whatsapp.net`` when missing.
        """
        _assert_scalar_string(number, "number")
        contacts = [contact] if isinstance(contact, dict) else list(contact)

        normalized: list[dict[str, Any]] = []
        for ct in contacts:
            entry = dict(ct)
            if not entry.get("wuid"):
                phone = entry.get("phoneNumber") or number
                cleaned = "".join(c for c in str(phone) if c.isdigit())
                if cleaned:
                    entry["wuid"] = jid(cleaned)
            normalized.append({k: v for k, v in entry.items() if v is not None})

        body = compact({"number": number, "contact": normalized})
        spec = RequestSpec("POST", evo_path("message", "sendContact", self.instance), body)
        return self._execute(spec, verbose=self._resolve_verbose(verbose))

    def send_reaction(
        self: ClientCore,
        key: dict[str, Any],
        reaction: str,
        *,
        verbose: bool | None = None,
    ) -> Any:
        """React to a message with an emoji.

        Args:
            key: ``{"remoteJid": ..., "fromMe": ..., "id": ...}`` of the target.
            reaction: Emoji string; use ``""`` to remove an existing reaction.
        """
        if not isinstance(key, dict) or not key.get("id"):
            raise EvolutionConfigError('key must be a dict with at least an "id" field.')
        if not isinstance(reaction, str):
            raise EvolutionConfigError("reaction must be a string (emoji or empty string).")
        body = {"key": key, "reaction": reaction}
        spec = RequestSpec("POST", evo_path("message", "sendReaction", self.instance), body)
        return self._execute(spec, verbose=self._resolve_verbose(verbose))

    def send_buttons(
        self: ClientCore,
        number: str,
        title: str,
        description: str,
        footer: str,
        buttons: list[dict[str, Any]],
        *,
        delay: int | None = None,
        link_preview: bool | None = None,
        mentions_everyone: bool | None = None,
        verbose: bool | None = None,
    ) -> Any:
        """Send a message with interactive buttons.

        Warning:
            Interactive buttons are **not supported on the Baileys connector** and
            may be discontinued; this works on the Cloud API connector only. A
            :class:`UserWarning` is emitted. Consider :meth:`send_poll` instead.
        """
        warnings.warn(_BAILEYS_WARNING.format(kind="buttons"), UserWarning, stacklevel=2)
        _assert_scalar_string(number, "number")
        _assert_scalar_string(title, "title")
        _assert_scalar_string(description, "description")
        _assert_scalar_string(footer, "footer")
        if not isinstance(buttons, list) or len(buttons) == 0:
            raise EvolutionConfigError("buttons must be a non-empty list of button definitions.")
        body = compact(
            {
                "number": number,
                "title": title,
                "description": description,
                "footer": footer,
                "buttons": buttons,
                "delay": delay,
                "linkPreview": link_preview,
                "mentionsEveryOne": mentions_everyone,
            }
        )
        spec = RequestSpec("POST", evo_path("message", "sendButtons", self.instance), body)
        return self._execute(spec, verbose=self._resolve_verbose(verbose))

    def send_poll(
        self: ClientCore,
        number: str,
        name: str,
        values: list[str],
        *,
        selectable_count: int = 1,
        verbose: bool | None = None,
    ) -> Any:
        """Send a poll (question with selectable options).

        Args:
            number: Recipient with country code.
            name: Question text.
            values: Poll options (minimum 2).
            selectable_count: How many options a user may select (default 1).
        """
        _assert_scalar_string(number, "number")
        _assert_scalar_string(name, "name")
        if not isinstance(values, (list, tuple)) or len(values) < 2:
            raise EvolutionConfigError("values must be a list with at least 2 options.")
        body = {
            "number": number,
            "name": name,
            "values": list(values),
            "selectableCount": int(selectable_count),
        }
        spec = RequestSpec("POST", evo_path("message", "sendPoll", self.instance), body)
        return self._execute(spec, verbose=self._resolve_verbose(verbose))

    def send_list(
        self: ClientCore,
        number: str,
        title: str,
        description: str,
        button_text: str,
        sections: list[dict[str, Any]],
        *,
        footer: str = "",
        delay: int | None = None,
        verbose: bool | None = None,
    ) -> Any:
        """Send an interactive list message.

        Args:
            number: Recipient with country code.
            title: List message title.
            description: List body text.
            button_text: Text on the list button (e.g. ``"View options"``).
            sections: Section dicts, each ``{"title": ..., "rows": [...]}`` where a
                row is ``{"title": ..., "description"?: ..., "rowId"?: ...}``.
            footer: Footer text. Defaults to ``""`` (the API requires ``footerText``).

        Warning:
            Interactive lists are **not supported on the Baileys connector** and
            may be discontinued; this works on the Cloud API connector only. A
            :class:`UserWarning` is emitted. Consider :meth:`send_poll` instead.
        """
        warnings.warn(_BAILEYS_WARNING.format(kind="list messages"), UserWarning, stacklevel=2)
        _assert_scalar_string(number, "number")
        _assert_scalar_string(title, "title")
        _assert_scalar_string(description, "description")
        _assert_scalar_string(button_text, "button_text")
        if not isinstance(sections, list) or len(sections) == 0:
            raise EvolutionConfigError("sections must be a non-empty list of section definitions.")
        body = compact(
            {
                "number": number,
                "title": title,
                "description": description,
                "buttonText": button_text,
                "footerText": footer,
                "sections": sections,
                "delay": delay,
            }
        )
        spec = RequestSpec("POST", evo_path("message", "sendList", self.instance), body)
        return self._execute(spec, verbose=self._resolve_verbose(verbose))
