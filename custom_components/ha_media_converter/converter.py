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
    """Return a safe basename and extension for an accepted image file."""
    basename = Path(filename.replace("\\", "/")).name
    extension = Path(basename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise InvalidImageError(
            "Only .heic, .heif, .jpg, .jpeg, and .png files are supported."
        )

    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(basename).stem).strip("_")
    if not stem:
        stem = "image"
    return stem[:100], extension


def convert_and_store(data: bytes, filename: str, media_dir: Path) -> str:
    """Convert HEIF images and save accepted images in the media directory."""
    from PIL import Image, ImageOps, UnidentifiedImageError

    stem, extension = sanitize_filename(filename)
    is_heif = extension in {".heic", ".heif"}
    if is_heif:
        import pillow_heif

        pillow_heif.register_heif_opener()

    try:
        with Image.open(io.BytesIO(data)) as image:
            expected_formats = {
                ".heic": {"HEIF"},
                ".heif": {"HEIF"},
                ".jpg": {"JPEG", "MPO"},
                ".jpeg": {"JPEG", "MPO"},
                ".png": {"PNG"},
            }[extension]
            if image.format not in expected_formats:
                raise InvalidImageError(
                    f"The file contents were detected as {image.format or 'unknown'}, "
                    "which does not match the filename extension."
                )
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ImageTooLargeError(
                    f"Images must be {MAX_IMAGE_PIXELS:,} pixels or smaller."
                )
            image.load()
            if is_heif:
                converted = ImageOps.exif_transpose(image).convert("RGB")
                output = io.BytesIO()
                converted.save(output, format="JPEG", quality=92, optimize=True)
                stored_data = output.getvalue()
                stored_extension = ".jpg"
            else:
                stored_data = data
                stored_extension = extension
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
        stored_name = f"{stem}{suffix}{stored_extension}"
        stored_path = media_dir / stored_name

        stored_created = False
        try:
            with stored_path.open("xb") as stored_file:
                stored_created = True
                stored_file.write(stored_data)
        except FileExistsError:
            continue
        except OSError:
            if stored_created:
                stored_path.unlink(missing_ok=True)
            raise

        return stored_name

    raise OSError("Could not find a free filename in the media folder.")
