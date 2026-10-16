# HA Media Converter

A Home Assistant custom integration that uploads HEIC/HEIF photos, converts
them to JPEG, and saves both the original and converted image in Home
Assistant's local media folder.

## Features

- An authenticated uploader on the integration's configuration page.
- Upload one or several `.heic` / `.heif` files from the browser.
- JPEG output is saved beside the original in the `media` folder.
- Existing files are never overwritten; repeated names get a numeric suffix.
- Uploads are limited to 20 MB and 40 megapixels per image.

## Install with HACS

1. Add this repository as a custom repository in HACS, using the **Integration**
   category.
2. Install **HA Media Converter** from HACS.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**, search for
   **HA Media Converter**, and add it.
5. Open **HA Media Converter** under **Settings → Devices & services** and
   use its configuration page to upload your photos.

The uploader is administrator-only and does not add a sidebar item. The
original HEIC/HEIF and converted JPEG remain in the local media folder and are
available through Home Assistant's media browser.

## Requirements and limits

The integration installs `pillow-heif` as a Python dependency. Conversion is
performed locally by Home Assistant; images are not sent to an external
service. HEIC/HEIF input is converted to RGB JPEG, so any transparency in an
input image is not preserved.

## Development

Copy `custom_components/ha_media_converter` into the Home Assistant
configuration's `custom_components` directory, restart Home Assistant, then
add the integration through **Settings → Devices & services**.
