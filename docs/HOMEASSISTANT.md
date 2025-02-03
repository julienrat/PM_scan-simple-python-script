# 🏠 PMScan - Intégration Home Assistant

## 📝 Description
Cette intégration permet de connecter votre capteur PMScan à Home Assistant via Bluetooth. Elle permet de :
- Visualiser les données en temps réel
- Créer des automatisations
- Enregistrer l'historique des mesures
- Configurer des alertes

## ⚙️ Prérequis
- Home Assistant 2023.8.0 ou plus récent
- Un adaptateur Bluetooth compatible
- Un capteur PMScan

## 🚀 Installation

### Méthode 1 : HACS (recommandée)
1. Assurez-vous d'avoir [HACS](https://hacs.xyz/) installé
2. Allez dans HACS > Intégrations > Menu (⋮) > Dépôts personnalisés
3. Ajoutez le dépôt : `https://github.com/julienrat/PM_scan-simple-python-script`
4. Cliquez sur "PMScan" dans la liste des intégrations
5. Cliquez sur "Télécharger"
6. Redémarrez Home Assistant

### Méthode 2 : Installation manuelle
1. Téléchargez le dossier `custom_components/pmscan`
2. Copiez-le dans le dossier `custom_components` de votre installation Home Assistant
3. Redémarrez Home Assistant

## 🔧 Configuration
1. Allez dans Configuration > Intégrations
2. Cliquez sur le bouton "+" (Ajouter une intégration)
3. Recherchez "PMScan"
4. Sélectionnez votre appareil PMScan dans la liste
5. L'intégration va automatiquement créer les entités

## 📊 Entités créées

### Capteurs
- `sensor.pmscan_pm1_0` : Concentration PM1.0 (μg/m³)
- `sensor.pmscan_pm2_5` : Concentration PM2.5 (μg/m³)
- `sensor.pmscan_pm10_0` : Concentration PM10.0 (μg/m³)
- `sensor.pmscan_temperature` : Température (°C)
- `sensor.pmscan_humidity` : Humidité (%)

## 🎨 Exemples d'utilisation

### Carte Lovelace
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

### Automatisation d'alerte
```yaml
alias: Alerte Qualité Air
description: "Envoie une notification quand le PM2.5 dépasse 25 μg/m³"
trigger:
  - platform: numeric_state
    entity_id: sensor.pmscan_pm2_5
    above: 25
action:
  - service: notify.mobile_app
    data:
      message: "⚠️ Attention ! Niveau PM2.5 élevé : {{ states('sensor.pmscan_pm2_5') }} μg/m³"
```

## 🐛 Dépannage

### Problèmes courants
1. Bluetooth non détecté :
   - Vérifiez que le PMScan est allumé
   - Vérifiez que le Bluetooth est activé dans Home Assistant
   - Vérifiez que l'adaptateur Bluetooth est compatible
   
2. Données manquantes :
   - Vérifiez la portée Bluetooth
   - Vérifiez les logs de Home Assistant
   - Redémarrez le PMScan

### Logs
Pour activer les logs détaillés, ajoutez à `configuration.yaml` :
```yaml
logger:
  default: info
  logs:
    custom_components.pmscan: debug
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
- [Guide Bluetooth dans Home Assistant](https://www.home-assistant.io/integrations/bluetooth/)
- [Guide des composants personnalisés](https://developers.home-assistant.io/docs/creating_component_index) 