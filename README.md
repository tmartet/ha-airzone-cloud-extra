# Airzone Cloud Extra

Composant personnalisé Home Assistant qui ajoute les appareils Airzone ignorés par l'intégration officielle **Airzone Cloud** :

- **Capteur de qualité d'air AirQ** (`az_airqsensor`) : CO₂, COV totaux, PM1 / PM2.5 / PM10, pression, humidité, température, score et qualité (globale et par mesure), états purification / ventilation / relais VMC / mode nuit, et sélecteur du mode de ventilation (off / on / auto).
- **Pince de consommation** (`az_energy_clamp`) : une entité par valeur numérique renvoyée par l'API (unités à préciser), plus un capteur « Données brutes ».

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
- Le changement de mode de ventilation (PATCH `aq_vent_mode_conf`) n'a pas encore été validé sur une installation réelle.
- La pince énergie publie ses mesures toutes les 60 min ; ses champs ne sont pas encore typés (unités, classe énergie).
