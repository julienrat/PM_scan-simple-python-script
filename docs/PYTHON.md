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