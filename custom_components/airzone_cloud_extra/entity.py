"""Entité de base."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODEL_NAMES, SOURCE_DOMAIN, TYPE_AIRQ, TYPE_SYSTEM
from .coordinator import AirzoneExtraCoordinator


class AirzoneExtraEntity(CoordinatorEntity[AirzoneExtraCoordinator]):
    """Entité liée à un appareil Airzone découvert."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AirzoneExtraCoordinator, device_id: str, key: str) -> None:
        super().__init__(coordinator)
        self.device_id = device_id
        self.key = key
        info = coordinator.data[device_id]
        default_name = "Qualité d'air" if info["type"] == TYPE_AIRQ else "Conso Airzone"
        self._attr_unique_id = f"{device_id}_{key}"
        if info["type"] == TYPE_SYSTEM:
            # HA ne permet pas d'ajouter une entité à l'appareil d'une autre intégration :
            # appareil propre, relié à celui de la centrale officielle via via_device.
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device_id)},
                manufacturer="Airzone",
                model=MODEL_NAMES.get(TYPE_SYSTEM),
                name="Centrale Airzone",
                via_device=(SOURCE_DOMAIN, device_id),
            )
            return
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Airzone",
            model=MODEL_NAMES.get(info["type"], info["type"]),
            name=info.get("name") or default_name,
        )

    @property
    def status(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get(self.device_id, {}).get("status", {})

    @property
    def config(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get(self.device_id, {}).get("config", {})

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.status.get("isConnected", True) is not False
            and self.key_present
        )

    @property
    def key_present(self) -> bool:
        return True
