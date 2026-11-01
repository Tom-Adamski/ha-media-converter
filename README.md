# HA Media Converter

A Home Assistant custom integration that uploads HEIC/HEIF photos, converts
them to JPEG, and saves them in Home Assistant's local media folder. JPEG and
PNG images are also accepted and saved unchanged.

## Features

- An uploader on the integration's Settings page and as a Lovelace card.
- Upload `.heic`, `.heif`, `.jpg`, `.jpeg`, and `.png` files from the browser.
- Choose the destination folder in Home Assistant's local `media` folder.
- HEIC/HEIF input is converted to JPEG; JPEG and PNG input is saved unchanged.
- Existing files are never overwritten; repeated names get a numeric suffix.
- Uploads are limited to 20 MB and 40 megapixels per image.

## Install with HACS

1. Add this repository as a custom repository in HACS, using the **Integration**
   category.
2. Install **HA Media Converter** from HACS.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**, search for
   **HA Media Converter**, and add it.
5. Open **HA Media Converter** under **Settings → Devices & services** to use
   the uploader panel.
6. To use the Lovelace card, add `/ha_media_converter/panel.js` as a JavaScript
   module resource under **Settings → Dashboards → Resources**, then add this
   card to a dashboard:

   ```yaml
   type: custom:ha-media-converter-card
   ```

The converted JPEG is available through Home Assistant's media browser. The
uploader lists existing folders beneath the local media folder.

## Requirements and limits

The integration installs `pillow-heif` as a Python dependency. Conversion is
performed locally by Home Assistant; images are not sent to an external
service. HEIC/HEIF input is converted to RGB JPEG, so any transparency in an
input image is not preserved. JPEG and PNG files retain their original bytes.

## Development

Copy `custom_components/ha_media_converter` into the Home Assistant
configuration's `custom_components` directory, restart Home Assistant, then
add the integration through **Settings → Devices & services**.

Run the tests with the Home Assistant version pinned in `requirements.txt`:

```sh
python -m unittest discover -s tests
```

The integration tests exercise setup and config-flow behavior against the
installed Home Assistant APIs, so run them before deploying changes.
