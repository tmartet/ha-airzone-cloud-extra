"""Coordinateur : interroge l'API Airzone Cloud via la session de l'intégration officielle."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SOURCE_ENTRY_ID, CONFIG_TYPES, SCAN_INTERVAL, SUPPORTED_TYPES

_LOGGER = logging.getLogger(__name__)

API_V1 = "api/v1"


class AirzoneExtraCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Récupère l'état des appareils Airzone non gérés par l'intégration officielle.

    data = {device_id: {"type", "name", "ws_id", "status": {...}}}
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="airzone_cloud_extra",
            update_interval=SCAN_INTERVAL,
        )
        self.source_entry_id: str = entry.data[CONF_SOURCE_ENTRY_ID]
        self.installation_id: str | None = None
        self.devices: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------ helpers
    def _get_api(self):
        """Renvoie l'objet AirzoneCloudApi de l'intégration officielle."""
        src = self.hass.config_entries.async_get_entry(self.source_entry_id)
        if src is None or src.state is not ConfigEntryState.LOADED:
            raise UpdateFailed("L'intégration Airzone Cloud n'est pas chargée")
        coordinator = getattr(src, "runtime_data", None)
        api = getattr(coordinator, "airzone", None)
        if api is None:
            raise UpdateFailed("Impossible d'accéder au client Airzone Cloud")
        self.installation_id = src.data.get("id")
        return api

    async def _discover(self, api) -> None:
        """Repère les appareils non supportés dans les données brutes de l'installation."""
        raw = api.raw_data() if hasattr(api, "raw_data") else {}
        inst = (raw.get("installations") or {}).get(self.installation_id)
        if inst is None:
            inst = await api.api_request(
                "GET", f"{API_V1}/installations/{self.installation_id}"
            )
        found: dict[str, dict[str, Any]] = {}
        for group in inst.get("groups", []):
            for dev in group.get("devices", []):
                if dev.get("type") in SUPPORTED_TYPES | CONFIG_TYPES:
                    found[dev["device_id"]] = {
                        "type": dev["type"],
                        "name": dev.get("name") or "",
                        "ws_id": dev.get("ws_id"),
                    }
        if not found:
            _LOGGER.warning("Aucun capteur AirQ ni pince énergie trouvé dans l'installation")
        self.devices = found

    async def _get_status(self, api, device_id: str) -> dict[str, Any]:
        params = urlencode({"installation_id": self.installation_id, "type": "user"})
        res = await api.api_request(
            "GET", f"{API_V1}/devices/{device_id}/status?{params}"
        )
        # Certaines réponses encapsulent l'état dans une clé "status"
        if isinstance(res, dict) and isinstance(res.get("status"), dict) and len(res) <= 2:
            return res["status"]
        return res or {}

    async def _get_config(self, api, device_id: str) -> dict[str, Any]:
        """Configuration (paramètres avancés comme Q-Adapt) d'un appareil."""
        res: dict[str, Any] = {}
        for req_type in ("user", "advanced"):
            params = urlencode({"installation_id": self.installation_id, "type": req_type})
            try:
                res = await api.api_request(
                    "GET", f"{API_V1}/devices/{device_id}/config?{params}"
                ) or {}
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Config %s (%s) impossible : %s", device_id, req_type, err)
                continue
            if "qadapt_conf" in res:
                break
        return res

    # ------------------------------------------------------------------ update
    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        api = self._get_api()
        try:
            if not self.devices:
                await self._discover(api)
            data: dict[str, dict[str, Any]] = {}
            for device_id, info in self.devices.items():
                previous = (self.data or {}).get(device_id, {})
                if info["type"] in CONFIG_TYPES:
                    config = await self._get_config(api, device_id) or previous.get("config", {})
                    data[device_id] = {**info, "status": {}, "config": config}
                    continue
                try:
                    status = await self._get_status(api, device_id)
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Lecture %s impossible : %s", device_id, err)
                    status = previous.get("status", {})
                data[device_id] = {**info, "status": status}
            return data
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Erreur API Airzone Cloud : {err}") from err

    # ------------------------------------------------------------------ write
    async def async_set_param(self, device_id: str, param: str, value: Any) -> None:
        """Modifie un paramètre d'un appareil (PATCH /devices/{id})."""
        api = self._get_api()
        await api.api_request(
            "PATCH",
            f"{API_V1}/devices/{device_id}",
            json={
                "param": param,
                "value": value,
                "installation_id": self.installation_id,
            },
        )
        await self.async_request_refresh()
