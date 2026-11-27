"""Sélecteurs Airzone Cloud Extra."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import TYPE_AIRQ, TYPE_SYSTEM
from .coordinator import AirzoneExtraCoordinator
from .entity import AirzoneExtraEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AirzoneExtraCoordinator = entry.runtime_data
    entities: list[SelectEntity] = []
    for device_id, info in coordinator.data.items():
        if info["type"] == TYPE_AIRQ and "aq_vent_mode_conf" in info.get("status", {}):
            entities.append(AirzoneVentModeSelect(coordinator, device_id, "aq_vent_mode_conf"))
        if info["type"] == TYPE_SYSTEM and info.get("config", {}).get("qadapt_values"):
            entities.append(AirzoneQAdaptSelect(coordinator, device_id, "qadapt_conf"))
    async_add_entities(entities)


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


class AirzoneQAdaptSelect(AirzoneExtraEntity, SelectEntity):
    """Q-Adapt : adaptation du débit (vitesse du ventilateur) de l'unité gainable.

    Valeurs Airzone : standard, silence, min, max, power.
    """

    _attr_translation_key = "qadapt"
    _attr_icon = "mdi:fan-speed-2"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and bool(self.config.get("qadapt_values"))

    @property
    def options(self) -> list[str]:
        return self.config.get("qadapt_values") or ["standard", "silence", "min", "max", "power"]

    @property
    def current_option(self) -> str | None:
        return self.config.get("qadapt_conf")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_param(self.device_id, "qadapt_conf", option)
