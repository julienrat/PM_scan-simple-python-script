import asyncio
from bleak import BleakClient, BleakScanner
import struct
import time

# UUIDs des caractéristiques (correction du format)
REAL_TIME_DATA_UUID = "f3641901-00b0-4240-ba50-05ca45bf8abc"  # UUID corrigé
CURRENT_TIME_UUID = "f3641906-00b0-4240-ba50-05ca45bf8abc"    # UUID corrigé

# Adresse MAC de l'appareil
DEVICE_ADDRESS = "54:F8:2A:33:97:1A"

def parse_real_time_data(data):
    """Parse les données reçues du capteur"""
    # Décode les données selon le format spécifié
    timestamp, state, cmd, particles, pm1_0, pm2_5, pm10_0, temp, humidity, _ = struct.unpack("<IBBHHHHHHh", data)
    
    return {
        "timestamp": timestamp,
        "pm1_0": pm1_0 / 10.0,  # Division par 10 comme spécifié
        "pm2_5": pm2_5 / 10.0,
        "pm10_0": pm10_0 / 10.0,
        "temperature": temp / 10.0,
        "humidity": humidity / 10.0
    }

def notification_handler(sender, data):
    """Gère les notifications reçues du capteur"""
    parsed_data = parse_real_time_data(data)
    print("\033[2J\033[H")  # Efface l'écran
    print("=== PMScan Données en temps réel ===")
    print(f"PM1.0: {parsed_data['pm1_0']:.1f} µg/m³")
    print(f"PM2.5: {parsed_data['pm2_5']:.1f} µg/m³")
    print(f"PM10.0: {parsed_data['pm10_0']:.1f} µg/m³")
    print(f"Température: {parsed_data['temperature']:.1f}°C")
    print(f"Humidité: {parsed_data['humidity']:.1f}%")

async def scan_devices():
    """Scan et permet la sélection d'un appareil Bluetooth"""
    print("Recherche des appareils Bluetooth...")
    devices = await BleakScanner.discover()
    
    # Filtrer et afficher les appareils trouvés
    valid_devices = []
    print("\nAppareils trouvés:")
    
    for i, device in enumerate(devices):
        if device.name:  # Ne montrer que les appareils avec un nom
            print(f"{i+1}. {device.name} ({device.address})")
            valid_devices.append(device)
    
    if not valid_devices:
        print("Aucun appareil trouvé!")
        return None
    
    # Demander à l'utilisateur de choisir un appareil
    while True:
        try:
            choice = input("\nChoisissez un appareil (1-{}), ou 'q' pour quitter: ".format(len(valid_devices)))
            if choice.lower() == 'q':
                return None
            
            choice = int(choice)
            if 1 <= choice <= len(valid_devices):
                return valid_devices[choice-1]
            else:
                print("Choix invalide. Réessayez.")
        except ValueError:
            print("Entrée invalide. Veuillez entrer un numéro.")

async def main():
    # Scan et sélection de l'appareil
    device = await scan_devices()
    if not device:
        print("Opération annulée.")
        return
    
    print(f"\nConnexion à {device.name} ({device.address})...")
    
    try:
        async with BleakClient(device) as client:
            print("Connecté!")

            # Configuration des notifications
            await client.start_notify(REAL_TIME_DATA_UUID, notification_handler)
            
            # Envoi du timestamp actuel pour démarrer l'acquisition
            current_time = int(time.time())
            await client.write_gatt_char(CURRENT_TIME_UUID, struct.pack("<I", current_time))
            
            print("Réception des données... (Ctrl+C pour arrêter)")
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nArrêt...")
    except Exception as e:
        print(f"Erreur de connexion: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 