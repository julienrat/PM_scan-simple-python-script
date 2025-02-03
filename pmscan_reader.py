"""
Script de lecture pour le capteur PMScan.
Ce script permet de lire les données en temps réel d'un capteur PMScan via Bluetooth Low Energy (BLE).
Il affiche les mesures de qualité d'air (PM1.0, PM2.5, PM10.0), la température, l'humidité,
l'état de la batterie et la qualité de l'air avec un code couleur correspondant à la LED du capteur.
"""

import asyncio
from bleak import BleakClient, BleakScanner
import struct
import time

# UUIDs des caractéristiques BLE du PMScan
# Format: Base UUID = f3641900-00b0-4240-ba50-05ca45bf8abc
# Les autres UUIDs suivent le même format en incrémentant les 2 derniers chiffres de la première partie
PMSCAN_SERVICE_UUID = "f3641900-00b0-4240-ba50-05ca45bf8abc"  # Service principal
REAL_TIME_DATA_UUID = "f3641901-00b0-4240-ba50-05ca45bf8abc"  # Données temps réel (20 bytes)
MEMORY_DATA_UUID = "f3641902-00b0-4240-ba50-05ca45bf8abc"     # Données en mémoire
TEMP_HUMID_ALERT_UUID = "f3641903-00b0-4240-ba50-05ca45bf8abc"  # Alertes température/humidité
BATTERY_LEVEL_UUID = "f3641904-00b0-4240-ba50-05ca45bf8abc"   # Niveau batterie (%)
BATTERY_CHARGING_UUID = "f3641905-00b0-4240-ba50-05ca45bf8abc"  # État de charge (0-3)
CURRENT_TIME_UUID = "f3641906-00b0-4240-ba50-05ca45bf8abc"    # Configuration horloge (timestamp)
ACQUISITION_INTERVAL_UUID = "f3641907-00b0-4240-ba50-05ca45bf8abc"  # Intervalle d'acquisition
POWER_MODE_UUID = "f3641908-00b0-4240-ba50-05ca45bf8abc"      # Mode de fonctionnement
TEMP_HUMID_THRESHOLD_UUID = "f3641909-00b0-4240-ba50-05ca45bf8abc"  # Seuils température/humidité
DISPLAY_SETTINGS_UUID = "f364190a-00b0-4240-ba50-05ca45bf8abc"  # Configuration affichage
BATTERY_HEARTBEAT_UUID = "f364190b-00b0-4240-ba50-05ca45bf8abc"  # Batterie heartbeat

# États possibles de la charge de la batterie
BATTERY_STATES = {
    0: "Non branché",    # Pas de chargeur connecté
    1: "Pré-charge",     # Phase initiale de charge
    2: "En charge",      # Charge normale en cours
    3: "Chargé"         # Charge complète
}

# Seuils de qualité de l'air pour PM10 (en µg/m³)
AIR_QUALITY_THRESHOLDS = {
    10: ("EXCELLENTE", "\033[32m", "Verte"),     # < 10 µg/m³
    30: ("BONNE", "\033[33m", "Jaune"),          # < 30 µg/m³
    50: ("MOYENNE", "\033[38;5;208m", "Orange"), # < 50 µg/m³
    80: ("MAUVAISE", "\033[31m", "Rouge"),       # < 80 µg/m³
    float('inf'): ("TRÈS MAUVAISE", "\033[35m", "Violette")  # ≥ 80 µg/m³
}

def parse_real_time_data(data):
    """
    Parse les données reçues du capteur PMScan.
    
    Format des données (20 bytes):
    - Timestamp (4 bytes): Horodatage Unix
    - State (1 byte): État du capteur
    - Command (1 byte): Commande en cours
    - Particles count (2 bytes): Nombre de particules par ml
    - PM1.0 (2 bytes): Concentration en µg/m³ (divisé par 10)
    - PM2.5 (2 bytes): Concentration en µg/m³ (divisé par 10)
    - PM10.0 (2 bytes): Concentration en µg/m³ (divisé par 10)
    - Temperature (2 bytes): Température en °C (divisé par 10)
    - Humidity (2 bytes): Humidité en % (divisé par 10)
    - Reserved (2 bytes): Non utilisé
    
    Returns:
        dict: Données parsées ou None si erreur
    """
    # Vérification de la taille des données
    if len(data) != 20:
        print(f"ERREUR: Taille des données invalide: {len(data)} bytes (attendu: 20 bytes)")
        return None
    
    # Affichage des données brutes pour débogage
    print("Données brutes:", ' '.join(f'{x:02X}' for x in data))
    
    # Décode les données selon le format spécifié
    timestamp, state, cmd, particles_count, pm1_0, pm2_5, pm10_0, temp, humidity = struct.unpack("<IBBHHHHHHxx", data)
    
    # Vérification des valeurs PM pendant le démarrage (0xFFFF = capteur en initialisation)
    if pm1_0 == 0xFFFF or pm2_5 == 0xFFFF or pm10_0 == 0xFFFF:
        print("ATTENTION: Capteur en phase de démarrage, valeurs PM non valides")
        return None
    
    # Calcul et vérification des valeurs
    humidity_value = humidity / 10.0
    if humidity_value > 100:
        print(f"ATTENTION: Valeur d'humidité anormale détectée: {humidity_value}%")
        humidity_value = min(humidity_value, 100)  # Limite à 100%
    
    temp_value = temp / 10.0
    if temp_value < -40 or temp_value > 85:
        print(f"ATTENTION: Température hors limites: {temp_value}°C")
        print("Note: La température est celle du PCB interne, pas de l'environnement")
    
    return {
        "timestamp": timestamp,
        "state": state,
        "command": cmd,
        "particles_count": particles_count,
        "pm1_0": pm1_0 / 10.0,
        "pm2_5": pm2_5 / 10.0,
        "pm10_0": pm10_0 / 10.0,
        "temperature": temp_value,
        "humidity": humidity_value
    }

def get_air_quality_info(pm10_value):
    """
    Détermine la qualité de l'air et la couleur correspondante basée sur la valeur PM10.
    
    Args:
        pm10_value (float): Valeur PM10 en µg/m³
        
    Returns:
        tuple: (qualité, code_couleur_terminal, couleur_led)
    """
    for threshold, (quality, color_code, led_color) in AIR_QUALITY_THRESHOLDS.items():
        if pm10_value < threshold:
            return quality, color_code, led_color
    return AIR_QUALITY_THRESHOLDS[float('inf')]

def notification_handler(sender, data):
    """
    Gère les notifications reçues du capteur et met à jour l'affichage.
    Affiche toutes les données en temps réel, y compris l'état de la batterie
    et la qualité de l'air avec le code couleur correspondant.
    """
    parsed_data = parse_real_time_data(data)
    if parsed_data is None:
        return
        
    print("\033[2J\033[H")  # Efface l'écran
    print("=== PMScan Données en temps réel ===")
    
    # Affichage des données de batterie et charge
    if hasattr(notification_handler, 'battery_level'):
        level = notification_handler.battery_level
        bars = int(level / 10)
        print("\nBatterie:")
        print("[" + "█" * bars + "░" * (10 - bars) + f"] {level}%")
    
    if hasattr(notification_handler, 'charging_state'):
        state = notification_handler.charging_state
        states = {
            0: "\033[31mNon branché\033[0m",      # Rouge
            1: "\033[33mPré-charge\033[0m",       # Jaune
            2: "\033[36mEn charge\033[0m",        # Cyan
            3: "\033[32mChargé\033[0m"            # Vert
        }
        print(f"État de charge : {states.get(state, f'Inconnu ({state})')}\n")
    
    # Affichage des données du capteur
    print(f"État: 0x{parsed_data['state']:02X}")
    print(f"Commande: 0x{parsed_data['command']:02X}")
    print(f"Particules (PM10.0): {parsed_data['particles_count']} /ml")
    print(f"PM1.0: {parsed_data['pm1_0']:.1f} µg/m³")
    print(f"PM2.5: {parsed_data['pm2_5']:.1f} µg/m³")
    print(f"PM10.0: {parsed_data['pm10_0']:.1f} µg/m³")
    print(f"Température PCB: {parsed_data['temperature']:.1f}°C")
    print(f"Humidité interne: {parsed_data['humidity']:.1f}%")
    
    # Affichage de la qualité de l'air avec code couleur
    quality, color_code, led_color = get_air_quality_info(parsed_data['pm10_0'])
    print(f"{color_code}Qualité de l'air: {quality} (LED {led_color})\033[0m")

def battery_notification_handler(sender, data):
    """
    Gère les notifications de niveau de batterie.
    Stocke le niveau dans une variable globale pour l'affichage principal.
    """
    level = data[0]
    notification_handler.battery_level = level

def charging_notification_handler(sender, data):
    """
    Gère les notifications d'état de charge.
    Stocke l'état dans une variable globale pour l'affichage principal.
    """
    state = data[0]
    notification_handler.charging_state = state

async def scan_devices():
    """
    Scanne les appareils Bluetooth disponibles et permet à l'utilisateur
    d'en sélectionner un dans la liste.
    
    Returns:
        BLEDevice: L'appareil sélectionné ou None si annulé
    """
    print("Recherche des appareils Bluetooth...")
    devices = await BleakScanner.discover()
    
    valid_devices = []
    print("\nAppareils trouvés:")
    
    for i, device in enumerate(devices):
        if device.name:  # Ne montrer que les appareils avec un nom
            print(f"{i+1}. {device.name} ({device.address})")
            valid_devices.append(device)
    
    if not valid_devices:
        print("Aucun appareil trouvé!")
        return None
    
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
    """
    Fonction principale qui gère la connexion au capteur PMScan et
    la réception des données en temps réel.
    """
    # Scan et sélection de l'appareil
    device = await scan_devices()
    if not device:
        print("Opération annulée.")
        return
    
    print(f"\nConnexion à {device.name} ({device.address})...")
    
    try:
        async with BleakClient(device) as client:
            print("Connecté!")

            # Configuration des notifications pour toutes les caractéristiques
            await client.start_notify(REAL_TIME_DATA_UUID, notification_handler)
            await client.start_notify(BATTERY_LEVEL_UUID, battery_notification_handler)
            await client.start_notify(BATTERY_CHARGING_UUID, charging_notification_handler)
            
            # Lecture initiale des informations de la batterie
            try:
                battery_level = await client.read_gatt_char(BATTERY_LEVEL_UUID)
                charging_state = await client.read_gatt_char(BATTERY_CHARGING_UUID)
                print(f"\nInformations batterie initiales :")
                battery_notification_handler(None, battery_level)
                charging_notification_handler(None, charging_state)
                print("-" * 40)
            except Exception as e:
                print(f"Erreur lors de la lecture de la batterie : {str(e)}")
            
            # Envoi du timestamp actuel pour synchroniser l'horloge
            current_time = int(time.time())
            await client.write_gatt_char(CURRENT_TIME_UUID, struct.pack("<I", current_time))
            
            print("\nRéception des données... (Ctrl+C pour arrêter)")
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nArrêt...")
    except Exception as e:
        print(f"Erreur de connexion: {str(e)}")

if __name__ == "__main__":
    # Affichage des informations de configuration au démarrage
    print("=== PMScan Reader ===")
    print("UUIDs configurés:")
    print(f"Service: {PMSCAN_SERVICE_UUID}")
    print(f"Données temps réel: {REAL_TIME_DATA_UUID}")
    print(f"Horloge: {CURRENT_TIME_UUID}")
    print(f"Niveau batterie: {BATTERY_LEVEL_UUID}")
    print(f"État charge: {BATTERY_CHARGING_UUID}")
    print("-" * 40)
    
    # Démarrage de la boucle principale
    asyncio.run(main()) 