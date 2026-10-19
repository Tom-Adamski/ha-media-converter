"""Constants for the HEIC media converter."""

DOMAIN = "ha_media_converter"
PANEL_TITLE = "HEIC Converter"
UPLOAD_URL = f"/api/{DOMAIN}/upload"
DESTINATIONS_URL = f"/api/{DOMAIN}/destinations"

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_EXTENSIONS = {".heic", ".heif"}
