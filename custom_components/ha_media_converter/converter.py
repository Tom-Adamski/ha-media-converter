"""Image conversion and safe storage helpers."""

from __future__ import annotations

import io
import re
from pathlib import Path

from .const import ALLOWED_EXTENSIONS, MAX_IMAGE_PIXELS


class InvalidImageError(ValueError):
    """The uploaded file is not a decodable HEIF image."""


class ImageTooLargeError(ValueError):
    """The uploaded image exceeds the supported pixel limit."""


def sanitize_filename(filename: str) -> tuple[str, str]:
    """Return a safe basename and extension for an uploaded HEIF file."""
    basename = Path(filename.replace("\\", "/")).name
    extension = Path(basename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise InvalidImageError("Only .heic and .heif files are supported.")

    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(basename).stem).strip("_")
    if not stem:
        stem = "image"
    return stem[:100], extension


def convert_and_store(data: bytes, filename: str, media_dir: Path) -> tuple[str, str]:
    """Convert a HEIF image to JPEG and save both files in the media directory."""
    from PIL import Image, ImageOps, UnidentifiedImageError
    import pillow_heif

    stem, extension = sanitize_filename(filename)
    pillow_heif.register_heif_opener()

    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "HEIF":
                raise InvalidImageError("The uploaded file is not a HEIC/HEIF image.")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ImageTooLargeError(
                    f"Images must be {MAX_IMAGE_PIXELS:,} pixels or smaller."
                )
            image.load()
            converted = ImageOps.exif_transpose(image).convert("RGB")
            output = io.BytesIO()
            converted.save(output, format="JPEG", quality=92, optimize=True)
            jpeg_data = output.getvalue()
    except Image.DecompressionBombError as err:
        raise ImageTooLargeError(
            f"Images must be {MAX_IMAGE_PIXELS:,} pixels or smaller."
        ) from err
    except ImageTooLargeError:
        raise
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as err:
        raise InvalidImageError(
            "The uploaded file could not be decoded as HEIC/HEIF."
        ) from err

    media_dir.mkdir(parents=True, exist_ok=True)
    for index in range(10_000):
        suffix = "" if index == 0 else f"_{index}"
        original_name = f"{stem}{suffix}{extension}"
        converted_name = f"{stem}{suffix}.jpg"
        original_path = media_dir / original_name
        converted_path = media_dir / converted_name

        original_created = False
        try:
            with original_path.open("xb") as original_file:
                original_created = True
                original_file.write(data)
        except FileExistsError:
            continue
        except OSError:
            if original_created:
                original_path.unlink(missing_ok=True)
            raise

        converted_created = False
        try:
            with converted_path.open("xb") as converted_file:
                converted_created = True
                converted_file.write(jpeg_data)
        except FileExistsError:
            original_path.unlink(missing_ok=True)
            continue
        except OSError:
            original_path.unlink(missing_ok=True)
            if converted_created:
                converted_path.unlink(missing_ok=True)
            raise

        return original_name, converted_name

    raise OSError("Could not find a free filename in the media folder.")
