"""Home Assistant HEIC media converter integration."""

from pathlib import Path

from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .http import UploadView


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up HTTP resources and the configuration panel."""
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
    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path=DOMAIN,
        config_panel_domain=DOMAIN,
        webcomponent_name="ha-media-converter-panel",
        module_url=f"/{DOMAIN}/panel.js",
        embed_iframe=False,
        require_admin=False,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True
