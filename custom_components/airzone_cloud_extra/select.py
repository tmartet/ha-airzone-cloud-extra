"""Sélecteurs Airzone Cloud Extra."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import TYPE_AIRQ
from .coordinator import AirzoneExtraCoordinator
from .entity import AirzoneExtraEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AirzoneExtraCoordinator = entry.runtime_data
    async_add_entities(
        AirzoneVentModeSelect(coordinator, device_id, "aq_vent_mode_conf")
        for device_id, info in coordinator.data.items()
        if info["type"] == TYPE_AIRQ and "aq_vent_mode_conf" in info.get("status", {})
    )


class AirzoneVentModeSelect(AirzoneExtraEntity, SelectEntity):
    """Mode de ventilation piloté par la qualité d'air (off / on / auto)."""

    _attr_name = "Mode ventilation qualité d'air"
    _attr_icon = "mdi:fan-auto"

    @property
    def options(self) -> list[str]:
        return self.status.get("aq_vent_mode_values") or ["off", "on", "auto"]

    @property
    def current_option(self) -> str | None:
        return self.status.get("aq_vent_mode_conf")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_param(self.device_id, "aq_vent_mode_conf", option)
