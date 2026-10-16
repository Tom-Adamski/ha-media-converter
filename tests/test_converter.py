"""Tests for safe HEIF filename handling."""

import unittest

from custom_components.ha_media_converter.converter import (
    InvalidImageError,
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


if __name__ == "__main__":
    unittest.main()
