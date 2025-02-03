# 🌟 PMScan Reader

## 📝 Description
PMScan Reader est un programme Python permettant de lire les données en temps réel d'un capteur de particules fines PMScan via Bluetooth Low Energy (BLE). Le programme permet de mesurer la qualité de l'air en affichant les concentrations de particules PM1.0, PM2.5 et PM10.0, ainsi que la température et l'humidité.

Le PMScan est un appareil portable et autonome qui permet de :
- 📊 Mesurer la qualité de l'air en temps réel
- 🔋 Fonctionner sur batterie rechargeable via USB-C
- 📱 Se connecter sans fil via Bluetooth
- 💾 Stocker les données en mémoire interne (selon modèle)

## ⚙️ Prérequis
- Python 3.7+
- Bibliothèques Python :
  - bleak (pour la communication BLE)
  - asyncio (pour la gestion asynchrone)
  - struct (pour le décodage des données)
- Un appareil PMScan
- Un adaptateur Bluetooth compatible BLE

## 💻 Installation
1. Clonez ce dépôt :
```bash
git clone https://github.com/julienrat/PM_scan-simple-python-script.git
cd PM_scan-simple-python-script
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## ✨ Fonctionnalités
- 🔍 Scan et connexion automatique aux appareils PMScan disponibles
- 📊 Lecture en temps réel des données :
  - PM1.0 (μg/m³) : Particules de diamètre inférieur à 1.0 micromètre
  - PM2.5 (μg/m³) : Particules de diamètre inférieur à 2.5 micromètres
  - PM10.0 (μg/m³) : Particules de diamètre inférieur à 10 micromètres
  - Température (°C) : Température interne du boîtier
  - Humidité (%) : Humidité interne du boîtier
- 🔄 Affichage clair et actualisé des mesures
- 🤝 Gestion de la connexion/déconnexion Bluetooth
- 🔌 Détection automatique de la charge USB

## 🚀 Utilisation
1. Allumez votre capteur PMScan :
   - Appui long 3 secondes sur le bouton tactile
   - Attendez que l'indicateur PM devienne coloré (~15 sec)

2. Lancez le programme :
```bash
python pmscan_reader.py
```

3. Sélectionnez votre appareil PMScan dans la liste des appareils Bluetooth détectés
4. Les données seront affichées en temps réel à l'écran
5. Pour arrêter le programme, utilisez Ctrl+C

## 💡 Indicateurs du PMScan

### 📶 Indicateur de connexion BLE
- 🔵 Clignotant : En attente de connexion
- 🔵 Fixe : Connecté

### 🔋 Indicateur de batterie
Sans charge :
- 🔴 Rouge fixe : Batterie faible

En charge :
- 🟠 Orange clignotant : En charge
- 🟢 Vert fixe : Charge complète

### 🌈 Indicateur PM (qualité de l'air)
- ⚪ Blanc : Démarrage du capteur (~15 sec)
- 🟢 Vert : PM10 < 10 μg/m³ (Excellente qualité)
- 🟡 Jaune : PM10 entre 10 et 30 μg/m³ (Bonne qualité)
- 🟠 Orange : PM10 entre 30 et 50 μg/m³ (Qualité moyenne)
- 🔴 Rouge : PM10 entre 50 et 80 μg/m³ (Mauvaise qualité)
- 🟣 Violet : PM10 > 80 μg/m³ (Très mauvaise qualité)

## 🔧 Notes techniques
- 📡 Communication BLE :
  - Données temps réel : f3641901-00b0-4240-ba50-05ca45bf8abc
  - Configuration temps : f3641906-00b0-4240-ba50-05ca45bf8abc
- 🌡️ Les données de température et d'humidité sont des mesures internes au boîtier
- 📊 Les valeurs PM sont divisées par 10 pour obtenir les mesures réelles en μg/m³
- 💾 Capacité de stockage interne (selon modèle) : jusqu'à 6145 enregistrements
- ⚡ Autonomie : variable selon l'utilisation et la configuration

## ❓ Dépannage
- 🔍 Si le capteur n'est pas détecté :
  - Vérifiez qu'il est bien allumé (LED clignotante)
  - Vérifiez que le Bluetooth de votre ordinateur est activé
  - Assurez-vous d'être à portée du capteur (< 10m)
- 🔌 En cas de problème de connexion :
  - Éteignez et rallumez le capteur
  - Redémarrez le programme
  - Vérifiez que le capteur n'est pas déjà connecté à un autre appareil
- 🔋 Si la batterie est faible :
  - Rechargez via le port USB-C
  - Utilisez un chargeur 5V standard

## 📄 Licence
Ce programme est distribué sous licence libre.

## 📬 Contact
Pour toute question ou problème :
- 🐛 Ouvrez une issue sur le dépôt GitHub
- 📧 Contactez le développeur via GitHub
- 📚 Consultez la documentation complète du PMScan

## 🙏 Remerciements
Merci à tous les contributeurs qui ont participé à l'amélioration de ce projet !
