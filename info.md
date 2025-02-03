# PMScan Air Quality Monitor

[![GitHub Release][releases-shield]][releases]
[![HACS Default][hacs-shield]][hacs]
[![License][license-shield]](LICENSE)

Intégration pour le capteur de qualité de l'air PMScan.

## Caractéristiques

- 📊 Mesure des particules fines PM1.0, PM2.5, PM10.0
- 🌡️ Température et humidité
- 🔄 Mise à jour automatique des données
- 🔍 Découverte automatique des appareils
- 📱 Interface native Home Assistant

## Installation

1. Assurez-vous d'avoir [HACS](https://hacs.xyz) installé
2. Ajoutez ce dépôt comme intégration personnalisée dans HACS
3. Recherchez "PMScan" dans les intégrations HACS
4. Cliquez sur "Télécharger"
5. Redémarrez Home Assistant
6. Allez dans Configuration > Intégrations
7. Cliquez sur "+" et recherchez "PMScan"

## Configuration

L'intégration détecte automatiquement les appareils PMScan disponibles.
Sélectionnez simplement votre appareil dans la liste lors de la configuration.

## Support

- 🐛 [Signaler un bug](https://github.com/julienrat/PM_scan-simple-python-script/issues)
- 💡 [Proposer une amélioration](https://github.com/julienrat/PM_scan-simple-python-script/issues)

[releases-shield]: https://img.shields.io/github/release/julienrat/PM_scan-simple-python-script.svg
[releases]: https://github.com/julienrat/PM_scan-simple-python-script/releases
[hacs-shield]: https://img.shields.io/badge/HACS-Default-orange.svg
[hacs]: https://github.com/hacs/integration
[license-shield]: https://img.shields.io/github/license/julienrat/PM_scan-simple-python-script.svg 