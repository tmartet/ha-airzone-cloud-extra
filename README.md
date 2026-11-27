# Airzone Cloud Extra

Composant personnalisé Home Assistant qui ajoute les appareils Airzone ignorés par l'intégration officielle **Airzone Cloud** :

- **Capteur de qualité d'air AirQ** (`az_airqsensor`) : CO₂, COV totaux, PM1 / PM2.5 / PM10, pression, humidité, température, score et qualité (globale et par mesure), états purification / ventilation / relais VMC / mode nuit, et sélecteur du mode de ventilation (off / on / auto).
- **Pince de consommation** (`az_energy_clamp`) : énergie consommée / renvoyée sur la dernière heure (kWh), puissance (kW), courant (A), tension (V), et deux **compteurs cumulés** (`total_increasing`, kWh) utilisables dans le tableau de bord Énergie.

- **Système (centrale)** : sélecteur **Q-Adapt** (`qadapt_conf` : standard / silence / min / max / power), qui règle l'adaptation du débit de l'unité gainable. Ajouté à l'appareil système existant de l'intégration officielle. Nécessite un compte administrateur de l'installation.

## Fonctionnement

Aucun identifiant à saisir : le composant réutilise la session de l'intégration officielle `airzone_cloud` et interroge l'API Airzone Cloud toutes les 60 s (`GET /api/v1/devices/{id}/status`).

## Installation

### Via HACS
1. HACS → menu ⋮ → **Dépôts personnalisés** → `https://github.com/tmartet/ha-airzone-cloud-extra`, catégorie **Intégration**.
2. Installer **Airzone Cloud Extra**, puis redémarrer Home Assistant.
3. Paramètres → Appareils et services → **Ajouter une intégration** → *Airzone Cloud Extra*.

### Manuelle
Copier `custom_components/airzone_cloud_extra` dans `/config/custom_components/`, redémarrer, puis ajouter l'intégration.

## Prérequis
- L'intégration officielle **Airzone Cloud** configurée et chargée.

## Limites connues
- Le mode de ventilation est modifié via `PATCH /devices/{id}` (`param`, `value`, `installation_id`), conforme à la doc Airzone.
- La pince publie ses mesures toutes les 60 min. D'après la [doc Airzone](https://developers.airzonecloud.com/docs/web-api/), l'énergie publiée est celle de la dernière heure en kWh ; les compteurs cumulés l'additionnent à chaque nouvelle période (`energy_period_end_dt`).
- `power_total`, `current_total` et `voltage_total` ne sont pas documentés : unités déduites (kW, A, V).
