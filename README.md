# PMScan Reader

## Description
PMScan Reader est un programme Python permettant de lire les données en temps réel d'un capteur de particules fines PMScan via Bluetooth Low Energy (BLE). Le programme permet de mesurer la qualité de l'air en affichant les concentrations de particules PM1.0, PM2.5 et PM10.0, ainsi que la température et l'humidité.

## Prérequis
- Python 3.7+
- Bibliothèques Python :
  - bleak (pour la communication BLE)
  - asyncio (pour la gestion asynchrone)
  - struct (pour le décodage des données)

## Installation
```bash
pip install bleak asyncio
```

## Fonctionnalités
- Scan et connexion automatique aux appareils PMScan disponibles
- Lecture en temps réel des données :
  - PM1.0 (μg/m³)
  - PM2.5 (μg/m³)
  - PM10.0 (μg/m³)
  - Température (°C)
  - Humidité (%)
- Affichage clair et actualisé des mesures
- Gestion de la connexion/déconnexion Bluetooth

## Utilisation
1. Allumez votre capteur PMScan (appui long 3 secondes sur le bouton tactile)
2. Lancez le programme :
```bash
python pmscan_reader.py
```
3. Sélectionnez votre appareil PMScan dans la liste des appareils Bluetooth détectés
4. Les données seront affichées en temps réel
5. Pour arrêter le programme, utilisez Ctrl+C

## Indicateurs du PMScan

### Indicateur de connexion BLE
- Clignotant : En attente de connexion
- Fixe : Connecté

### Indicateur de batterie
Sans charge :
- Rouge fixe : Batterie faible

En charge :
- Orange clignotant : En charge
- Vert fixe : Charge complète

### Indicateur PM (qualité de l'air)
- Blanc : Démarrage du capteur (~15 sec)
- Vert : PM10 < 10 μg/m³
- Jaune : PM10 entre 10 et 30 μg/m³
- Orange : PM10 entre 30 et 50 μg/m³
- Rouge : PM10 entre 50 et 80 μg/m³
- Violet : PM10 > 80 μg/m³

## Notes techniques
- Le programme utilise les UUIDs suivants pour la communication BLE :
  - Données temps réel : f3641901-00b0-4240-ba50-05ca45bf8abc
  - Configuration temps : f3641906-00b0-4240-ba50-05ca45bf8abc
- Les données de température et d'humidité sont des mesures internes au boîtier et non de l'environnement extérieur
- Les valeurs PM sont divisées par 10 pour obtenir les mesures réelles en μg/m³

## Dépannage
- Si le capteur n'est pas détecté, vérifiez qu'il est bien allumé (LED clignotante)
- En cas de problème de connexion, éteignez et rallumez le capteur
- Assurez-vous que le Bluetooth de votre ordinateur est activé

## Licence
Ce programme est distribué sous licence libre.

## Contact
Pour toute question ou problème, veuillez ouvrir une issue sur le dépôt GitHub.
