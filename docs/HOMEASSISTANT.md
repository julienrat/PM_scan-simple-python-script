# 🏠 PMScan - Intégration Home Assistant

## 📝 Description
Cette intégration permet de connecter votre capteur PMScan à Home Assistant via MQTT. Elle permet de :
- Visualiser les données en temps réel
- Créer des automatisations
- Enregistrer l'historique des mesures
- Configurer des alertes

## ⚙️ Prérequis
- Home Assistant installé et configuré
- MQTT Broker configuré dans Home Assistant
- Python 3.7+ sur la machine qui exécutera le script
- Un capteur PMScan
- Une connexion Bluetooth

## 🚀 Installation

1. Installez les dépendances Python :
```bash
pip install -r requirements.txt
```

2. Configurez le fichier `config.yaml` :
```yaml
mqtt:
  broker: homeassistant.local  # Adresse de votre broker MQTT
  port: 1883                   # Port MQTT
  username: homeassistant      # Utilisateur MQTT
  password: "votre_mot_de_passe"  # Mot de passe MQTT
  topic_prefix: homeassistant/sensor/pmscan

device:
  address: null  # Sera détecté automatiquement
  name: PMScan
  model: PMScan Air Quality Monitor
  manufacturer: PMScan

update_interval: 60  # Secondes
```

3. Lancez le script :
```bash
python pmscan_homeassistant.py
```

## 📊 Entités créées dans Home Assistant

### Capteurs
- `sensor.pmscan_pm1_0` : Concentration PM1.0 (μg/m³)
- `sensor.pmscan_pm2_5` : Concentration PM2.5 (μg/m³)
- `sensor.pmscan_pm10_0` : Concentration PM10.0 (μg/m³)
- `sensor.pmscan_temperature` : Température (°C)
- `sensor.pmscan_humidity` : Humidité (%)

### Attributs
Chaque capteur inclut :
- Horodatage de la dernière mise à jour
- Qualité du signal Bluetooth
- État de la batterie (si disponible)

## 🎨 Personnalisation dans Home Assistant

### Exemple de carte Lovelace
```yaml
type: vertical-stack
cards:
  - type: entities
    title: PMScan
    entities:
      - entity: sensor.pmscan_pm2_5
      - entity: sensor.pmscan_pm10_0
      - entity: sensor.pmscan_temperature
      - entity: sensor.pmscan_humidity
  
  - type: history-graph
    title: Historique PM2.5
    entities:
      - entity: sensor.pmscan_pm2_5
```

### Exemple d'automatisation
```yaml
automation:
  - alias: "Alerte Qualité Air"
    trigger:
      platform: numeric_state
      entity_id: sensor.pmscan_pm2_5
      above: 25
    action:
      - service: notify.mobile_app
        data:
          message: "Attention ! PM2.5 élevé"
```

## 🔧 Configuration avancée

### Multiples capteurs
Pour utiliser plusieurs PMScan :
1. Créez des copies du fichier config.yaml
2. Modifiez le `topic_prefix` pour chaque appareil
3. Lancez une instance du script pour chaque configuration

### Intégration dans InfluxDB
Ajoutez dans votre configuration Home Assistant :
```yaml
influxdb:
  host: localhost
  include:
    entities:
      - sensor.pmscan_pm2_5
      - sensor.pmscan_pm10_0
```

## 🐛 Dépannage

### Problèmes courants
1. MQTT non connecté :
   - Vérifiez les identifiants MQTT
   - Vérifiez que le broker est accessible
   
2. Bluetooth non détecté :
   - Vérifiez que le PMScan est allumé
   - Vérifiez les droits Bluetooth
   - Redémarrez le script

3. Données manquantes :
   - Vérifiez la portée Bluetooth
   - Vérifiez les logs du script
   - Vérifiez la configuration MQTT

### Logs
Pour activer les logs détaillés :
```bash
python pmscan_homeassistant.py --debug
```

## 📈 Graphiques recommandés

### Mini-graphique
```yaml
type: custom:mini-graph-card
entities:
  - sensor.pmscan_pm2_5
hours_to_show: 24
points_per_hour: 4
```

### Graphique détaillé
```yaml
type: statistics-graph
entities:
  - sensor.pmscan_pm2_5
  - sensor.pmscan_pm10_0
hours_to_show: 168
```

## 🔔 Alertes recommandées

### Seuils OMS
```yaml
binary_sensor:
  - platform: template
    sensors:
      air_quality_warning:
        friendly_name: "Alerte Qualité Air"
        value_template: >
          {{ states('sensor.pmscan_pm2_5')|float > 25 or 
             states('sensor.pmscan_pm10_0')|float > 50 }}
```

## 📚 Ressources
- [Documentation Home Assistant](https://www.home-assistant.io/)
- [Documentation MQTT](https://www.home-assistant.io/integrations/mqtt/)
- [Guide Lovelace](https://www.home-assistant.io/lovelace/) 