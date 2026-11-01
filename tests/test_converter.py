"""Tests for safe HEIF filename handling."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from custom_components.ha_media_converter.converter import (
    InvalidImageError,
    convert_and_store,
    sanitize_filename,
)


class SanitizeFilenameTests(unittest.TestCase):
    """Validate upload filenames before they reach the filesystem."""

    def test_strips_path_and_normalizes_extension(self):
        self.assertEqual(
            sanitize_filename(r"C:\Users\home\Summer Photo.HEIC"),
            ("Summer_Photo", ".heic"),
        )

    def test_replaces_empty_or_unsafe_stem(self):
        self.assertEqual(sanitize_filename("!!!.heif"), ("image", ".heif"))

    def test_rejects_non_heif_extensions(self):
        with self.assertRaises(InvalidImageError):
            sanitize_filename("photo.jpg")


class ConvertAndStoreTests(unittest.TestCase):
    """Validate converted-file storage behavior."""

    def test_saves_only_converted_image(self):
        converted = Mock()
        converted.save.side_effect = lambda output, **kwargs: output.write(b"jpeg")
        image = MagicMock(format="HEIF", width=1, height=1)

        with tempfile.TemporaryDirectory() as directory:
            media_dir = Path(directory)
            with (
                patch.dict(sys.modules, {"pillow_heif": Mock()}),
                patch("PIL.Image.open", return_value=image),
                patch("PIL.ImageOps.exif_transpose", return_value=converted),
            ):
                result = convert_and_store(b"heic", "photo.heic", media_dir)

            self.assertEqual(result, "photo.jpg")
            self.assertEqual([path.name for path in media_dir.iterdir()], ["photo.jpg"])
            self.assertEqual((media_dir / "photo.jpg").read_bytes(), b"jpeg")

    def test_saves_jpeg_and_png_inputs_unchanged(self):
        for filename, image_format, data in (
            ("photo.jpg", "JPEG", b"original jpeg bytes"),
            ("photo.png", "PNG", b"original png bytes"),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                image = MagicMock(format=image_format, width=1, height=1)
                with patch("PIL.Image.open", return_value=image):
                    result = convert_and_store(data, filename, Path(directory))

                self.assertEqual(result, filename)
                self.assertEqual((Path(directory) / filename).read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
