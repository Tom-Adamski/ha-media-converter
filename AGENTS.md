# Agent Context

## Project

HA Media Converter is a Home Assistant custom integration for uploading images through a Settings panel or Lovelace card. HEIC/HEIF images are converted locally to JPEG; JPEG and PNG files are stored unchanged. Files are saved under Home Assistant's local `media` directory. No image data is sent to an external service.

## Code Map

- `custom_components/ha_media_converter/__init__.py`: registers authenticated API views, serves the panel JavaScript, and registers the Settings panel.
- `config_flow.py`: creates one integration entry; only one entry is allowed.
- `const.py`: integration domain, API paths, accepted extensions, and upload/image limits.
- `http.py`: admin-only upload and destination-list APIs, multipart validation, destination path validation, and executor dispatch.
- `converter.py`: filename sanitization, image format and pixel checks, HEIF conversion, and collision-safe file creation.
- `www/panel.js`: Settings panel and Lovelace card UI; obtains a Home Assistant access token and calls the API.
- `tests/test_converter.py`: filename and conversion/storage behavior.
- `tests/test_integration.py`: setup/config-flow API compatibility and media destination behavior.

## Behavior and Constraints

- Supported extensions are `.heic`, `.heif`, `.jpg`, `.jpeg`, and `.png`. Verify decoded image format matches the extension; do not trust filenames alone.
- HEIC/HEIF is EXIF-oriented and converted to RGB JPEG. JPEG and PNG bytes are preserved unchanged.
- Uploads are limited to 20 MiB and images to 40 megapixels. Keep checks on the server side even if frontend validation is added.
- Never overwrite existing files. Storage uses exclusive creation and adds a numeric suffix on collisions.
- Only existing folders inside the local media directory can be selected. Preserve symlink/path traversal protections.
- Both API views require an authenticated administrator, regardless of panel visibility or client-side checks.
- Keep image decoding and filesystem work off the event loop by dispatching `convert_and_store` and destination listing through `hass.async_add_executor_job`.
- Preserve Home Assistant API compatibility; the pinned HA version is in `requirements.txt`.

## Development and Tests

Don't install locally / run any test.

For later reference :
- Install dependencies from `requirements.txt` in the development environment.
- Run tests with `python -m unittest discover -s tests`.
- Keep tests in the existing `unittest` style and extend the closest relevant test module for behavior changes.
- Keep changes focused on the integration and its existing frontend; update `README.md` when user-visible behavior or setup instructions change.
