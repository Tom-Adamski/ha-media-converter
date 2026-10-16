"""Config flow for the HEIC media converter."""

from homeassistant import config_entries

from .const import DOMAIN, PANEL_TITLE


class HaMediaConverterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the integration from the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the integration entry."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        return self.async_create_entry(title=PANEL_TITLE, data={})
