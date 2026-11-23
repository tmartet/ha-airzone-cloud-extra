"""Capteurs Airzone Cloud Extra."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    EntityCategory,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import META_KEYS, TYPE_AIRQ, TYPE_ENERGY_CLAMP
from .coordinator import AirzoneExtraCoordinator
from .entity import AirzoneExtraEntity

QUALITY_OPTIONS = ["good", "regular", "bad"]


@dataclass(frozen=True, kw_only=True)
class AirzoneExtraSensorDescription(SensorEntityDescription):
    sub_key: str | None = None  # pour les valeurs imbriquées, ex. aq_temp.celsius


M = SensorStateClass.MEASUREMENT

AIRQ_SENSORS: tuple[AirzoneExtraSensorDescription, ...] = (
    AirzoneExtraSensorDescription(key="aq_co2", name="CO₂", device_class=SensorDeviceClass.CO2,
                                  native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION, state_class=M),
    AirzoneExtraSensorDescription(key="aq_tvoc", name="COV totaux",
                                  device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
                                  native_unit_of_measurement=CONCENTRATION_PARTS_PER_BILLION, state_class=M),
    AirzoneExtraSensorDescription(key="aqpm1_0", name="PM1", device_class=SensorDeviceClass.PM1,
                                  native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, state_class=M),
    AirzoneExtraSensorDescription(key="aqpm2_5", name="PM2.5", device_class=SensorDeviceClass.PM25,
                                  native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, state_class=M),
    AirzoneExtraSensorDescription(key="aqpm10", name="PM10", device_class=SensorDeviceClass.PM10,
                                  native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, state_class=M),
    AirzoneExtraSensorDescription(key="aq_pressure", name="Pression", device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
                                  native_unit_of_measurement=UnitOfPressure.HPA, state_class=M),
    AirzoneExtraSensorDescription(key="humidity", name="Humidité", device_class=SensorDeviceClass.HUMIDITY,
                                  native_unit_of_measurement=PERCENTAGE, state_class=M),
    AirzoneExtraSensorDescription(key="aq_temp", sub_key="celsius", name="Température",
                                  device_class=SensorDeviceClass.TEMPERATURE,
                                  native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=M),
    AirzoneExtraSensorDescription(key="aq_score", name="Score qualité d'air", state_class=M, icon="mdi:air-filter"),
    AirzoneExtraSensorDescription(key="aq_quality", name="Qualité d'air", device_class=SensorDeviceClass.ENUM,
                                  options=QUALITY_OPTIONS, icon="mdi:air-filter"),
    *(
        AirzoneExtraSensorDescription(key=f"aq_{p}_score", name=f"Score {label}", state_class=M,
                                      entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False)
        for p, label in (("co2", "CO₂"), ("tvoc", "COV"), ("pm2_5", "PM2.5"), ("pm10", "PM10"),
                         ("temp", "température"), ("hum", "humidité"))
    ),
    *(
        AirzoneExtraSensorDescription(key=f"aq_{p}_quality", name=f"Qualité {label}", device_class=SensorDeviceClass.ENUM,
                                      options=QUALITY_OPTIONS, entity_category=EntityCategory.DIAGNOSTIC)
        for p, label in (("co2", "CO₂"), ("tvoc", "COV"), ("pm2_5", "PM2.5"), ("pm10", "PM10"),
                         ("temp", "température"), ("hum", "humidité"))
    ),
)


def _flatten(status: dict[str, Any]) -> dict[str, float | int]:
    """Aplati les valeurs numériques (un niveau d'imbrication)."""
    out: dict[str, float | int] = {}
    for k, v in status.items():
        if k in META_KEYS or isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            out[k] = v
        elif isinstance(v, dict):
            for sk, sv in v.items():
                if isinstance(sv, (int, float)) and not isinstance(sv, bool) and sk != "fah":
                    out[f"{k}.{sk}"] = sv
    return out


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AirzoneExtraCoordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for device_id, info in coordinator.data.items():
        status = info.get("status", {})
        if info["type"] == TYPE_AIRQ:
            entities += [
                AirzoneExtraSensor(coordinator, device_id, d)
                for d in AIRQ_SENSORS
                if d.key in status
            ]
        elif info["type"] == TYPE_ENERGY_CLAMP:
            # Champs encore inconnus : un capteur générique par valeur numérique
            entities += [
                AirzoneGenericSensor(coordinator, device_id, path) for path in _flatten(status)
            ]
        entities.append(AirzoneRawSensor(coordinator, device_id, "raw"))
    async_add_entities(entities)


class AirzoneExtraSensor(AirzoneExtraEntity, SensorEntity):
    entity_description: AirzoneExtraSensorDescription

    def __init__(self, coordinator, device_id, description: AirzoneExtraSensorDescription) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        val = self.status.get(self.entity_description.key)
        if self.entity_description.sub_key and isinstance(val, dict):
            val = val.get(self.entity_description.sub_key)
        if self.entity_description.device_class == SensorDeviceClass.ENUM and val not in QUALITY_OPTIONS:
            return None
        return val


class AirzoneGenericSensor(AirzoneExtraEntity, SensorEntity):
    """Valeur numérique brute (pince énergie) — unité à préciser."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device_id, path: str) -> None:
        super().__init__(coordinator, device_id, path.replace(".", "_"))
        self.path = path
        self._attr_name = path.replace("_", " ").replace(".", " ")

    @property
    def native_value(self):
        k, _, sk = self.path.partition(".")
        val = self.status.get(k)
        if sk and isinstance(val, dict):
            val = val.get(sk)
        return val if isinstance(val, (int, float)) and not isinstance(val, bool) else None


class AirzoneRawSensor(AirzoneExtraEntity, SensorEntity):
    """Diagnostic : toutes les données brutes en attributs (pour découvrir les champs)."""

    _attr_name = "Données brutes"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:code-json"

    @property
    def native_value(self):
        return len(self.status)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return dict(self.status)
