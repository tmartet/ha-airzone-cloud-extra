"""Config flow : choisit l'intégration Airzone Cloud source."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_SOURCE_ENTRY_ID, DOMAIN, SOURCE_DOMAIN


class AirzoneExtraConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        sources = {e.entry_id: e.title for e in self.hass.config_entries.async_entries(SOURCE_DOMAIN)}
        if not sources:
            return self.async_abort(reason="no_source")

        if user_input is None and len(sources) == 1:
            user_input = {CONF_SOURCE_ENTRY_ID: next(iter(sources))}

        if user_input is not None:
            source_id = user_input[CONF_SOURCE_ENTRY_ID]
            await self.async_set_unique_id(source_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Airzone Extra – {sources[source_id]}",
                data={CONF_SOURCE_ENTRY_ID: source_id},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_SOURCE_ENTRY_ID): vol.In(sources)}),
        )
