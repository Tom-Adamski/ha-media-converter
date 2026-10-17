"""Tests for Home Assistant integration and config-flow API compatibility."""

import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import create_autospec, patch

from homeassistant.components.http import HomeAssistantHTTP, StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.core import HomeAssistant

from custom_components.ha_media_converter import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ha_media_converter.config_flow import (
    HaMediaConverterConfigFlow,
)
from custom_components.ha_media_converter.const import DOMAIN, PANEL_TITLE
from custom_components.ha_media_converter.http import UploadView


class IntegrationSetupTests(unittest.IsolatedAsyncioTestCase):
    """Check integration setup against the installed Home Assistant APIs."""

    async def test_async_setup_registers_http_and_panel_resources(self):
        http = create_autospec(HomeAssistantHTTP, instance=True)
        hass = cast(HomeAssistant, SimpleNamespace(http=http))

        with patch(
            "custom_components.ha_media_converter.panel_custom.async_register_panel",
            autospec=True,
        ) as register_panel:
            self.assertTrue(await async_setup(hass, {}))

        http.register_view.assert_called_once()
        self.assertIsInstance(http.register_view.call_args.args[0], UploadView)
        self.assertIs(http.register_view.call_args.args[0].hass, hass)
        http.async_register_static_paths.assert_awaited_once_with(
            [
                StaticPathConfig(
                    f"/{DOMAIN}",
                    str(
                        Path(__file__).parents[1]
                        / "custom_components"
                        / DOMAIN
                        / "www"
                    ),
                    cache_headers=False,
                )
            ]
        )
        register_panel.assert_awaited_once_with(
            hass=hass,
            frontend_url_path=DOMAIN,
            config_panel_domain=DOMAIN,
            webcomponent_name="ha-media-converter-panel",
            module_url=f"/{DOMAIN}/panel.js",
            embed_iframe=False,
            require_admin=False,
        )

    async def test_entry_lifecycle_hooks_accept_home_assistant_arguments(self):
        hass = cast(HomeAssistant, object())
        entry = cast(ConfigEntry, object())

        self.assertTrue(await async_setup_entry(hass, entry))
        self.assertTrue(await async_unload_entry(hass, entry))


class ConfigFlowTests(unittest.IsolatedAsyncioTestCase):
    """Check config-flow behavior and its override signature."""

    async def test_user_step_creates_entry_when_not_configured(self):
        flow = HaMediaConverterConfigFlow()
        with patch.object(flow, "_async_current_entries", return_value=[]):
            with patch.object(
                flow, "async_create_entry", return_value={"type": "create_entry"}
            ) as create_entry:
                result = await flow.async_step_user()

        self.assertEqual(result, {"type": "create_entry"})
        create_entry.assert_called_once_with(title=PANEL_TITLE, data={})

    async def test_user_step_aborts_when_already_configured(self):
        flow = HaMediaConverterConfigFlow()
        with patch.object(
            flow, "_async_current_entries", return_value=[cast(ConfigEntry, object())]
        ):
            with patch.object(
                flow, "async_abort", return_value={"type": "abort"}
            ) as abort:
                result = await flow.async_step_user()

        self.assertEqual(result, {"type": "abort"})
        abort.assert_called_once_with(reason="already_configured")

    def test_user_step_signature_matches_home_assistant(self):
        expected = inspect.signature(ConfigFlow.async_step_user)
        actual = inspect.signature(HaMediaConverterConfigFlow.async_step_user)

        self.assertEqual(
            [
                (parameter.name, parameter.kind, parameter.default)
                for parameter in actual.parameters.values()
            ],
            [
                (parameter.name, parameter.kind, parameter.default)
                for parameter in expected.parameters.values()
            ],
        )


if __name__ == "__main__":
    unittest.main()
