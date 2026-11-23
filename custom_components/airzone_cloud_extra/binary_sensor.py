"""Capteurs binaires Airzone Cloud Extra."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import TYPE_AIRQ
from .coordinator import AirzoneExtraCoordinator
from .entity import AirzoneExtraEntity

AIRQ_BINARY: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(key="aq_active", name="Purification active", icon="mdi:air-purifier"),
    BinarySensorEntityDescription(key="aq_vent_active", name="Ventilation active",
                                  device_class=BinarySensorDeviceClass.RUNNING),
    BinarySensorEntityDescription(key="aq_relay_active", name="Relais VMC actif",
                                  device_class=BinarySensorDeviceClass.RUNNING),
    BinarySensorEntityDescription(key="aq_night_mode_active", name="Mode nuit actif", icon="mdi:weather-night"),
    BinarySensorEntityDescription(key="aq_measuring", name="Mesure en cours",
                                  entity_category=EntityCategory.DIAGNOSTIC),
)

CONNECTED = BinarySensorEntityDescription(
    key="isConnected", name="Connecté", device_class=BinarySensorDeviceClass.CONNECTIVITY,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AirzoneExtraCoordinator = entry.runtime_data
    entities = []
    for device_id, info in coordinator.data.items():
        status = info.get("status", {})
        descs = AIRQ_BINARY if info["type"] == TYPE_AIRQ else ()
        entities += [AirzoneExtraBinary(coordinator, device_id, d) for d in (*descs, CONNECTED) if d.key in status]
    async_add_entities(entities)


class AirzoneExtraBinary(AirzoneExtraEntity, BinarySensorEntity):
    def __init__(self, coordinator, device_id, description: BinarySensorEntityDescription) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        # Le capteur "Connecté" doit rester disponible même déconnecté
        if self.entity_description.key == "isConnected":
            return self.coordinator.last_update_success
        return super().available

    @property
    def is_on(self) -> bool | None:
        val = self.status.get(self.entity_description.key)
        return bool(val) if val is not None else None
