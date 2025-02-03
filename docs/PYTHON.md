# 🐍 PMScan - Script Python

## 📝 Description
PMScan Reader est un programme Python permettant de lire les données en temps réel d'un capteur de particules fines PMScan via Bluetooth Low Energy (BLE). Le programme permet de mesurer la qualité de l'air en affichant les concentrations de particules PM1.0, PM2.5 et PM10.0, ainsi que la température et l'humidité.

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

## 🔧 API Python

### Classe PMScanReader
```python
class PMScanReader:
    def __init__(self):
        """Initialise le lecteur PMScan."""
        self.device = None
        self.client = None

    async def scan_for_device(self):
        """Recherche les appareils PMScan disponibles."""
        devices = await BleakScanner.discover()
        pmscan_devices = [d for d in devices if d.name and "PMScan" in d.name]
        return pmscan_devices

    async def connect(self, device):
        """Connecte au PMScan spécifié."""
        self.device = device
        self.client = BleakClient(device)
        await self.client.connect()

    async def read_data(self):
        """Lit les données du PMScan."""
        data = await self.client.read_gatt_char(REAL_TIME_DATA_UUID)
        return self.parse_data(data)

    def parse_data(self, data):
        """Parse les données brutes du PMScan."""
        timestamp, _, _, _, pm1_0, pm2_5, pm10_0, temp, humidity, _ = struct.unpack("<IBBHHHHHHh", data)
        return {
            "pm1_0": pm1_0 / 10.0,
            "pm2_5": pm2_5 / 10.0,
            "pm10_0": pm10_0 / 10.0,
            "temperature": temp / 10.0,
            "humidity": humidity / 10.0
        }
```

### Exemple d'utilisation
```python
async def main():
    reader = PMScanReader()
    
    # Recherche des appareils
    devices = await reader.scan_for_device()
    if not devices:
        print("Aucun PMScan trouvé")
        return
    
    # Connexion au premier appareil trouvé
    await reader.connect(devices[0])
    
    # Lecture des données
    try:
        while True:
            data = await reader.read_data()
            print(f"PM2.5: {data['pm2_5']} μg/m³")
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await reader.disconnect()

asyncio.run(main())
```

## 🔧 Notes techniques

### Format des données
Les données sont reçues dans un format binaire structuré :
```python
struct.unpack("<IBBHHHHHHh", data)
```
- `I` : Timestamp (4 bytes)
- `BB` : Réservé (2 bytes)
- `H` : PM1.0 (2 bytes)
- `H` : PM2.5 (2 bytes)
- `H` : PM10.0 (2 bytes)
- `H` : Température (2 bytes)
- `H` : Humidité (2 bytes)
- `h` : Réservé (2 bytes)

### Conversion des valeurs
- Les valeurs PM sont divisées par 10 pour obtenir les μg/m³
- La température est divisée par 10 pour obtenir les °C
- L'humidité est divisée par 10 pour obtenir le pourcentage

## ❓ Dépannage

### Problèmes courants
1. Bluetooth non détecté :
   - Vérifiez que le PMScan est allumé (LED bleue clignotante)
   - Vérifiez que le Bluetooth est activé
   - Vérifiez les droits Bluetooth (Linux)

2. Erreurs de connexion :
   - Redémarrez le PMScan
   - Vérifiez qu'il n'est pas connecté ailleurs
   - Augmentez les délais de connexion

3. Données incorrectes :
   - Vérifiez la version du firmware
   - Assurez-vous que le capteur est stabilisé
   - Vérifiez la structure des données

### Logs de débogage
Pour activer les logs détaillés :
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Ressources
- [Documentation Bleak](https://bleak.readthedocs.io/)
- [Guide asyncio](https://docs.python.org/3/library/asyncio.html)
- [Documentation struct](https://docs.python.org/3/library/struct.html)

# Documentation Python du PMScan

Ce document décrit l'utilisation du script Python pour communiquer avec le capteur PMScan via Bluetooth Low Energy (BLE).

## Prérequis

- Python 3.7 ou supérieur
- Package `bleak` pour la communication BLE
- Un adaptateur Bluetooth compatible

Installation des dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation du script

Le script `pmscan_reader.py` permet de :
- Scanner et se connecter à un capteur PMScan
- Lire les données en temps réel (PM1.0, PM2.5, PM10.0)
- Afficher la température et l'humidité du capteur
- Monitorer l'état de la batterie et de la charge
- Visualiser la qualité de l'air avec un code couleur

### Lancement du script

```bash
python pmscan_reader.py
```

### Fonctionnalités

1. **Scan et connexion**
   - Le script scanne automatiquement les appareils Bluetooth
   - Liste les appareils PMScan trouvés
   - Permet de sélectionner l'appareil à connecter

2. **Affichage en temps réel**
   - État de la batterie avec barre de progression
   - État de charge avec code couleur :
     - Rouge : Non branché
     - Jaune : Pré-charge
     - Cyan : En charge
     - Vert : Chargé
   - Mesures de particules :
     - PM1.0 (µg/m³)
     - PM2.5 (µg/m³)
     - PM10.0 (µg/m³)
     - Nombre de particules par ml
   - Température du PCB
   - Humidité interne
   - Qualité de l'air avec code couleur LED :
     - Verte : Excellente (< 10 µg/m³)
     - Jaune : Bonne (< 30 µg/m³)
     - Orange : Moyenne (< 50 µg/m³)
     - Rouge : Mauvaise (< 80 µg/m³)
     - Violette : Très mauvaise (≥ 80 µg/m³)

3. **Gestion des erreurs**
   - Vérification de la validité des données
   - Messages d'erreur explicites
   - Gestion des déconnexions

## Format des données

### Données temps réel (20 bytes)

| Offset | Taille | Description | Format |
|--------|---------|-------------|---------|
| 0 | 4 | Timestamp | uint32 little-endian |
| 4 | 1 | État | uint8 |
| 5 | 1 | Commande | uint8 |
| 6 | 2 | Particules/ml | uint16 little-endian |
| 8 | 2 | PM1.0 | uint16 little-endian / 10 |
| 10 | 2 | PM2.5 | uint16 little-endian / 10 |
| 12 | 2 | PM10.0 | uint16 little-endian / 10 |
| 14 | 2 | Température | uint16 little-endian / 10 |
| 16 | 2 | Humidité | uint16 little-endian / 10 |
| 18 | 2 | Réservé | - |

### États de charge

| Valeur | État | Description |
|--------|------|-------------|
| 0 | Non branché | Pas de chargeur connecté |
| 1 | Pré-charge | Phase initiale de charge |
| 2 | En charge | Charge normale en cours |
| 3 | Chargé | Charge complète |

## UUIDs Bluetooth

Service principal : `f3641900-00b0-4240-ba50-05ca45bf8abc`

Caractéristiques :
- Données temps réel : `f3641901-00b0-4240-ba50-05ca45bf8abc`
- Données mémoire : `f3641902-00b0-4240-ba50-05ca45bf8abc`
- Alertes temp/humid : `f3641903-00b0-4240-ba50-05ca45bf8abc`
- Niveau batterie : `f3641904-00b0-4240-ba50-05ca45bf8abc`
- État charge : `f3641905-00b0-4240-ba50-05ca45bf8abc`
- Horloge : `f3641906-00b0-4240-ba50-05ca45bf8abc`
- Intervalle acquisition : `f3641907-00b0-4240-ba50-05ca45bf8abc`
- Mode alimentation : `f3641908-00b0-4240-ba50-05ca45bf8abc`
- Seuils temp/humid : `f3641909-00b0-4240-ba50-05ca45bf8abc`
- Config affichage : `f364190a-00b0-4240-ba50-05ca45bf8abc`
- Batterie heartbeat : `f364190b-00b0-4240-ba50-05ca45bf8abc`

## Exemple de sortie

```
=== PMScan Données en temps réel ===

Batterie:
[██████████] 100%
État de charge : Chargé

État: 0x00
Commande: 0x01
Particules (PM10.0): 123 /ml
PM1.0: 5.2 µg/m³
PM2.5: 8.7 µg/m³
PM10.0: 12.3 µg/m³
Température PCB: 24.5°C
Humidité interne: 45.2%
Qualité de l'air: BONNE (LED Jaune)
```

## Dépannage

1. **Erreur de connexion**
   - Vérifiez que le Bluetooth est activé
   - Assurez-vous que le capteur est allumé et à portée
   - Redémarrez le script

2. **Données invalides**
   - Attendez que le capteur termine son initialisation
   - Vérifiez que la batterie n'est pas trop faible
   - Redémarrez le capteur si nécessaire

3. **Problèmes de batterie**
   - Si le niveau est anormal, rechargez complètement
   - Vérifiez la connexion du chargeur
   - Attendez la fin de la phase de pré-charge 