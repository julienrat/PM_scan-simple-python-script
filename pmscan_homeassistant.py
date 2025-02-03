#!/usr/bin/env python3
import asyncio
from bleak import BleakClient, BleakScanner
import paho.mqtt.client as mqtt
import json
import struct
import time
import yaml
import os

# Configuration des UUIDs BLE
PMSCAN_SERVICE_UUID = "f3641900-00b0-4240-ba50-05ca45bf8abc"
REAL_TIME_DATA_UUID = "f3641901-00b0-4240-ba50-05ca45bf8abc"
CURRENT_TIME_UUID = "f3641906-00b0-4240-ba50-05ca45bf8abc"

# Configuration par défaut
DEFAULT_CONFIG = {
    'mqtt': {
        'broker': 'localhost',
        'port': 1883,
        'username': '',
        'password': '',
        'topic_prefix': 'homeassistant/sensor/pmscan'
    },
    'device': {
        'address': None,  # Sera rempli lors du scan
        'name': 'PMScan',
        'model': 'PMScan Air Quality Monitor',
        'manufacturer': 'PMScan'
    },
    'update_interval': 60  # Secondes
}

class PMScanHA:
    def __init__(self, config_path='config.yaml'):
        self.config = self.load_config(config_path)
        self.mqtt_client = None
        self.device = None
        self.setup_mqtt()

    def load_config(self, config_path):
        """Charge la configuration depuis un fichier YAML"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return {**DEFAULT_CONFIG, **config}
        return DEFAULT_CONFIG

    def setup_mqtt(self):
        """Configure la connexion MQTT"""
        self.mqtt_client = mqtt.Client()
        if self.config['mqtt']['username']:
            self.mqtt_client.username_pw_set(
                self.config['mqtt']['username'],
                self.config['mqtt']['password']
            )
        self.mqtt_client.connect(
            self.config['mqtt']['broker'],
            self.config['mqtt']['port']
        )
        self.mqtt_client.loop_start()

    def publish_discovery(self):
        """Publie les configurations de découverte pour Home Assistant"""
        sensors = {
            'pm1_0': {'name': 'PM1.0', 'unit': 'µg/m³', 'icon': 'mdi:air-filter'},
            'pm2_5': {'name': 'PM2.5', 'unit': 'µg/m³', 'icon': 'mdi:air-filter'},
            'pm10_0': {'name': 'PM10.0', 'unit': 'µg/m³', 'icon': 'mdi:air-filter'},
            'temperature': {'name': 'Temperature', 'unit': '°C', 'icon': 'mdi:thermometer'},
            'humidity': {'name': 'Humidity', 'unit': '%', 'icon': 'mdi:water-percent'}
        }

        base_topic = self.config['mqtt']['topic_prefix']
        device_info = {
            'identifiers': [f"pmscan_{self.config['device']['address']}"],
            'name': self.config['device']['name'],
            'model': self.config['device']['model'],
            'manufacturer': self.config['device']['manufacturer']
        }

        for sensor_id, sensor_data in sensors.items():
            config_topic = f"{base_topic}/{sensor_id}/config"
            config = {
                'name': f"{self.config['device']['name']} {sensor_data['name']}",
                'unique_id': f"pmscan_{self.config['device']['address']}_{sensor_id}",
                'state_topic': f"{base_topic}/state",
                'value_template': f"{{{{ value_json.{sensor_id} }}}}",
                'unit_of_measurement': sensor_data['unit'],
                'icon': sensor_data['icon'],
                'device': device_info
            }
            self.mqtt_client.publish(config_topic, json.dumps(config), retain=True)

    def parse_data(self, data):
        """Parse les données reçues du PMScan"""
        timestamp, _, _, _, pm1_0, pm2_5, pm10_0, temp, humidity, _ = struct.unpack("<IBBHHHHHHh", data)
        return {
            'pm1_0': pm1_0 / 10.0,
            'pm2_5': pm2_5 / 10.0,
            'pm10_0': pm10_0 / 10.0,
            'temperature': temp / 10.0,
            'humidity': humidity / 10.0
        }

    def publish_data(self, data):
        """Publie les données sur MQTT"""
        topic = f"{self.config['mqtt']['topic_prefix']}/state"
        self.mqtt_client.publish(topic, json.dumps(data))

    async def notification_handler(self, sender, data):
        """Gère les notifications reçues du PMScan"""
        try:
            parsed_data = self.parse_data(data)
            self.publish_data(parsed_data)
        except Exception as e:
            print(f"Erreur lors du traitement des données: {e}")

    async def scan_and_connect(self):
        """Scanne et se connecte au PMScan"""
        print("Recherche du PMScan...")
        
        if not self.config['device']['address']:
            devices = await BleakScanner.discover()
            for device in devices:
                if device.name and "PMScan" in device.name:
                    self.config['device']['address'] = device.address
                    break
            if not self.config['device']['address']:
                raise Exception("PMScan non trouvé")

        print(f"Connexion à {self.config['device']['address']}...")
        async with BleakClient(self.config['device']['address']) as client:
            print("Connecté!")
            self.publish_discovery()

            # Configuration des notifications
            await client.start_notify(
                REAL_TIME_DATA_UUID,
                self.notification_handler
            )

            # Envoi du timestamp
            timestamp = int(time.time())
            await client.write_gatt_char(
                CURRENT_TIME_UUID,
                struct.pack("<I", timestamp)
            )

            while True:
                await asyncio.sleep(1)

    async def run(self):
        """Boucle principale"""
        while True:
            try:
                await self.scan_and_connect()
            except Exception as e:
                print(f"Erreur de connexion: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    pmscan = PMScanHA()
    asyncio.run(pmscan.run()) 