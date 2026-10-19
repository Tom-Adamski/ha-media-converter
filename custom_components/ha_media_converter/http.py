"""Authenticated upload endpoint for HEIC images."""

from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath

from aiohttp import web
from homeassistant.helpers.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DESTINATIONS_URL, DOMAIN, MAX_UPLOAD_BYTES, UPLOAD_URL
from .converter import (
    ImageTooLargeError,
    InvalidImageError,
    convert_and_store,
    sanitize_filename,
)

_LOGGER = logging.getLogger(__name__)


class InvalidDestinationError(ValueError):
    """The requested destination is not a directory in the media folder."""


def _media_directory(hass: HomeAssistant) -> Path:
    """Return the configured local media directory."""
    media_dir = hass.config.media_dirs.get("local")
    if media_dir is None:
        media_dir = hass.config.path("media")
    return Path(media_dir)


def _list_destinations(media_dir: Path) -> list[str]:
    """Return existing subdirectories relative to the local media folder."""
    destinations: list[str] = []
    pending: list[tuple[Path, tuple[str, ...]]] = [(media_dir, ())]
    while pending:
        directory, parent_parts = pending.pop()
        try:
            children = sorted(
                directory.iterdir(), key=lambda path: path.name.casefold()
            )
        except FileNotFoundError:
            if directory == media_dir:
                return []
            raise
        for child in children:
            if child.is_symlink() or not child.is_dir():
                continue
            parts = (*parent_parts, child.name)
            destinations.append("/".join(parts))
            pending.append((child, parts))

    return sorted(destinations, key=str.casefold)


def _resolve_destination(media_dir: Path, relative_path: str) -> Path:
    """Resolve a selected existing directory without allowing escape from media."""
    if not relative_path:
        destination = media_dir
    else:
        parsed_path = PurePosixPath(relative_path)
        if (
            "\x00" in relative_path
            or parsed_path.is_absolute()
            or parsed_path.as_posix() != relative_path
            or not parsed_path.parts
            or any(part in {".", ".."} for part in parsed_path.parts)
        ):
            raise InvalidDestinationError("Choose a folder inside the media folder.")
        destination = media_dir.joinpath(*parsed_path.parts)

    resolved_root = media_dir.resolve()
    resolved_destination = destination.resolve()
    if (
        resolved_destination != resolved_root
        and resolved_root not in resolved_destination.parents
    ):
        raise InvalidDestinationError("Choose a folder inside the media folder.")
    if relative_path and not destination.is_dir():
        raise InvalidDestinationError("The selected media folder no longer exists.")
    return destination


class UploadView(HomeAssistantView):
    """Receive one HEIC/HEIF image and save its JPEG conversion."""

    url = UPLOAD_URL
    name = f"api:{DOMAIN}:upload"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the upload endpoint."""
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        """Save and convert the uploaded image."""
        user = request.get("hass_user")
        if user is None or not user.is_admin:
            return self.json_message(
                "Administrator access is required.", status_code=403
            )

        if (
            request.content_length is not None
            and request.content_length > MAX_UPLOAD_BYTES + 64 * 1024
        ):
            return self.json_message(
                "The upload exceeds the 20 MB limit.", status_code=413
            )

        try:
            multipart = await request.multipart()
        except (ValueError, AssertionError):
            return self.json_message("Upload a HEIC or HEIF file.", status_code=400)

        filename: str | None = None
        data: bytes | None = None
        destination = ""
        destination_received = False
        file_received = False
        async for part in multipart:
            if part.name == "destination":
                if destination_received or part.filename:
                    return self.json_message(
                        "Choose one media folder.", status_code=400
                    )
                destination_received = True
                destination_data = bytearray()
                while chunk := await part.read_chunk():
                    destination_data.extend(chunk)
                    if len(destination_data) > 1024:
                        return self.json_message(
                            "The selected media folder is invalid.", status_code=400
                        )
                try:
                    destination = destination_data.decode("utf-8")
                except UnicodeDecodeError:
                    return self.json_message(
                        "The selected media folder is invalid.", status_code=400
                    )
                continue
            if part.name != "file":
                return self.json_message("Upload a HEIC or HEIF file.", status_code=400)
            if file_received:
                return self.json_message("Upload one file at a time.", status_code=400)
            file_received = True
            if not part.filename:
                return self.json_message(
                    "The upload is missing a filename.", status_code=400
                )
            try:
                sanitize_filename(part.filename)
            except InvalidImageError as err:
                return self.json_message(str(err), status_code=400)

            chunks: list[bytes] = []
            size = 0
            while chunk := await part.read_chunk():
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    return self.json_message(
                        "The upload exceeds the 20 MB limit.", status_code=413
                    )
                chunks.append(chunk)
            filename = part.filename
            data = b"".join(chunks)

        if filename is None or data is None:
            return self.json_message("No file was uploaded.", status_code=400)

        media_dir = _media_directory(self.hass)
        try:
            target_dir = _resolve_destination(media_dir, destination)
        except InvalidDestinationError as err:
            return self.json_message(str(err), status_code=400)
        except OSError:
            _LOGGER.exception("Unable to resolve the selected media folder")
            return self.json_message(
                "Unable to access the selected media folder.", status_code=500
            )

        try:
            original_name, converted_name = await self.hass.async_add_executor_job(
                convert_and_store, data, filename, target_dir
            )
        except ImageTooLargeError as err:
            return self.json_message(str(err), status_code=413)
        except InvalidImageError as err:
            return self.json_message(str(err), status_code=400)
        except OSError:
            _LOGGER.exception("Unable to save HEIC conversion to the media folder")
            return self.json_message(
                "Unable to save the converted image.", status_code=500
            )

        return self.json(
            {
                "original": original_name,
                "converted": converted_name,
                "destination": destination,
            }
        )


class DestinationsView(HomeAssistantView):
    """List folders available under Home Assistant's local media directory."""

    url = DESTINATIONS_URL
    name = f"api:{DOMAIN}:destinations"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the destinations endpoint."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return available media subfolders."""
        user = request.get("hass_user")
        if user is None or not user.is_admin:
            return self.json_message(
                "Administrator access is required.", status_code=403
            )

        try:
            destinations = await self.hass.async_add_executor_job(
                _list_destinations, _media_directory(self.hass)
            )
        except OSError:
            _LOGGER.exception("Unable to list folders in the media directory")
            return self.json_message(
                "Unable to list media folders.", status_code=500
            )

        return self.json({"destinations": destinations})
