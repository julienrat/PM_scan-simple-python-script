# 🌟 PMScan - Capteur de Qualité de l'Air

## 📝 Description
PMScan est un capteur de qualité de l'air connecté qui mesure les particules fines (PM1.0, PM2.5, PM10.0), la température et l'humidité. Ce dépôt contient trois implémentations différentes pour utiliser votre capteur PMScan :

### 1. 🐍 [Script Python](docs/PYTHON.md)
- Lecture directe des données via Bluetooth Low Energy
- Interface en ligne de commande
- Idéal pour les projets DIY et l'intégration dans vos propres scripts

### 2. 🌐 [Interface Web](docs/WEB.md)
- Interface web moderne et responsive
- Connexion directe via Web Bluetooth
- Graphiques en temps réel
- Fonctionne dans le navigateur sans installation

### 3. 🏠 [Intégration Home Assistant](docs/HOMEASSISTANT.md)
- Intégration native dans Home Assistant
- Installation via HACS
- Découverte automatique des appareils
- Tableaux de bord et automatisations

## 🔧 Fonctionnalités Communes

### Mesures
- PM1.0 (μg/m³) : Particules < 1.0 micromètre
- PM2.5 (μg/m³) : Particules < 2.5 micromètres
- PM10.0 (μg/m³) : Particules < 10 micromètres
- Température (°C)
- Humidité (%)

### Indicateurs LED
- 📶 **Bluetooth** : 
  - 🔵 Clignotant : En attente
  - 🔵 Fixe : Connecté
- 🔋 **Batterie** :
  - 🔴 Rouge : Batterie faible
  - 🟠 Orange clignotant : En charge
  - 🟢 Vert : Chargé
- 🌈 **Qualité de l'air** :
  - 🟢 Vert : Excellente (PM10 < 10 μg/m³)
  - 🟡 Jaune : Bonne (PM10 10-30 μg/m³)
  - 🟠 Orange : Moyenne (PM10 30-50 μg/m³)
  - 🔴 Rouge : Mauvaise (PM10 50-80 μg/m³)
  - 🟣 Violet : Très mauvaise (PM10 > 80 μg/m³)

## 🚀 Par où commencer ?

1. **Utilisateur Home Assistant** :
   - Suivez le [guide d'installation Home Assistant](docs/HOMEASSISTANT.md)
   - Installation facile via HACS
   - Interface graphique intégrée

2. **Développeur Python** :
   - Consultez la [documentation Python](docs/PYTHON.md)
   - Exemples de code et API
   - Possibilités d'intégration

3. **Utilisateur Web** :
   - Accédez à la [documentation Web](docs/WEB.md)
   - Interface prête à l'emploi
   - Visualisation en temps réel

## 📚 Documentation Technique

### Communication Bluetooth
- Service UUID : f3641900-00b0-4240-ba50-05ca45bf8abc
- Caractéristiques :
  - Données temps réel : f3641901-00b0-4240-ba50-05ca45bf8abc
  - Configuration temps : f3641906-00b0-4240-ba50-05ca45bf8abc

### Format des Données
- Structure binaire : `<IBBHHHHHHh`
  - Timestamp (4 bytes)
  - Réservé (2 bytes)
  - PM1.0, PM2.5, PM10.0 (2 bytes chacun)
  - Température, Humidité (2 bytes chacun)
  - Réservé (2 bytes)

## 🤝 Contribution
Les contributions sont les bienvenues ! Voici comment vous pouvez aider :
- 🐛 Signaler des bugs
- 💡 Proposer des améliorations
- 📝 Améliorer la documentation
- 🔧 Soumettre des corrections

## 📄 Licence
Ce projet est sous licence libre.

## 📬 Contact
- 🐛 [Signaler un problème](https://github.com/julienrat/PM_scan-simple-python-script/issues)
- 📧 [Contacter le développeur](https://github.com/julienrat)

## 🙏 Remerciements
Merci à tous les contributeurs qui ont participé à ce projet !
