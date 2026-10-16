"""Authenticated upload endpoint for HEIC images."""

from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web
from homeassistant.helpers.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, MAX_UPLOAD_BYTES, UPLOAD_URL
from .converter import (
    ImageTooLargeError,
    InvalidImageError,
    convert_and_store,
    sanitize_filename,
)

_LOGGER = logging.getLogger(__name__)


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
        file_received = False
        async for part in multipart:
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

        media_dir = self.hass.config.media_dirs.get("local")
        if media_dir is None:
            media_dir = self.hass.config.path("media")

        try:
            original_name, converted_name = await self.hass.async_add_executor_job(
                convert_and_store, data, filename, Path(media_dir)
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
            }
        )
