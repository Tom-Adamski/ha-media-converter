"""Home Assistant HEIC media converter integration."""

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_TITLE
from .http import UploadView


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up HTTP and frontend resources."""
    integration_dir = Path(__file__).parent
    hass.http.register_view(UploadView(hass))
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                f"/{DOMAIN}",
                str(integration_dir / "www"),
                cache_headers=False,
            )
        ]
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up the converter panel."""
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon="mdi:image-convert",
        frontend_url_path=DOMAIN,
        config={
            "_panel_custom": {
                "name": "ha-media-converter-panel",
                "module_url": f"/{DOMAIN}/panel.js",
                "embed_iframe": False,
            }
        },
        require_admin=True,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Remove the converter panel."""
    frontend.async_remove_panel(hass, DOMAIN)
    return True
