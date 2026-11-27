"""Constantes pour Airzone Cloud Extra."""

from datetime import timedelta

DOMAIN = "airzone_cloud_extra"
SOURCE_DOMAIN = "airzone_cloud"

CONF_SOURCE_ENTRY_ID = "source_entry_id"

SCAN_INTERVAL = timedelta(seconds=60)

TYPE_AIRQ = "az_airqsensor"
TYPE_ENERGY_CLAMP = "az_energy_clamp"
TYPE_SYSTEM = "az_system"
SUPPORTED_TYPES = {TYPE_AIRQ, TYPE_ENERGY_CLAMP}
# Appareils déjà gérés par l'intégration officielle, dont on lit seulement la config
CONFIG_TYPES = {TYPE_SYSTEM}

MODEL_NAMES = {
    TYPE_AIRQ: "Capteur qualité d'air AirQ",
    TYPE_ENERGY_CLAMP: "Pince de consommation",
}

# Champs techniques jamais exposés comme capteurs génériques
META_KEYS = {
    "isConnected",
    "ws_connected",
    "name",
    "warnings",
    "errors",
    "ws_sched_param_indep",
    "vmc_sched_available",
}
