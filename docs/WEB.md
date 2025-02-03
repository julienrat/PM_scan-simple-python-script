# 🌟 PMScan Viewer

## 📱 Interface Web

Cette interface web permet de visualiser en temps réel les données de votre capteur PMScan via Bluetooth Low Energy (BLE).

### Fonctionnalités

- Connexion automatique aux capteurs PMScan
- Affichage en temps réel des mesures
- Graphique dynamique des concentrations
- Indicateur de qualité de l'air avec code couleur
- Monitoring de la batterie et de l'état de charge

### Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/julienrat/PM_scan-simple-python-script.git
cd PM_scan-simple-python-script
```

2. Ouvrez `index.html` dans votre navigateur

### Interface utilisateur

#### 🔌 État de connexion
- Bouton de connexion/déconnexion
- Statut de la connexion
- Nom et adresse du capteur

#### 🔋 État de la batterie
- Niveau de charge avec barre de progression
- État de charge :
  - 🔴 Non branché
  - 🟡 Pré-charge
  - 🔵 En charge
  - 🟢 Chargé

#### 📊 Mesures en temps réel
- PM1.0 (μg/m³)
- PM2.5 (μg/m³)
- PM10.0 (μg/m³)
- Température PCB (°C)
- Humidité interne (%)
- Nombre de particules par ml

#### 📈 Graphique
- Affichage des 3 mesures PM
- Mise à jour en temps réel
- Historique sur 50 points
- Légende colorée

#### 🌈 Qualité de l'air
Indicateur visuel basé sur PM10 :
- 💚 EXCELLENTE (< 10 μg/m³)
- 💛 BONNE (< 30 μg/m³)
- 🟧 MOYENNE (< 50 μg/m³)
- ❤️ MAUVAISE (< 80 μg/m³)
- 💜 TRÈS MAUVAISE (≥ 80 μg/m³)

### Compatibilité

- Chrome 56+ sur Android/Desktop
- Edge 79+ sur Windows
- Safari 14.1+ sur macOS/iOS

### Configuration requise

- Navigateur compatible Web Bluetooth
- Appareil avec Bluetooth Low Energy
- PMScan avec firmware récent

### Dépannage

1. **Bluetooth non détecté**
   - Vérifiez que le navigateur est compatible
   - Activez le Bluetooth sur votre appareil
   - Autorisez l'accès au Bluetooth

2. **Connexion impossible**
   - Vérifiez que le PMScan est allumé
   - Rapprochez-vous du capteur
   - Redémarrez le navigateur

3. **Données manquantes**
   - Attendez l'initialisation du capteur
   - Vérifiez la connexion Bluetooth
   - Rafraîchissez la page

### Notes techniques

Les données sont reçues via BLE avec les caractéristiques suivantes :

- Service : `f3641900-00b0-4240-ba50-05ca45bf8abc`
- Données temps réel : `f3641901-00b0-4240-ba50-05ca45bf8abc`
- Batterie : `f3641904-00b0-4240-ba50-05ca45bf8abc`
- État de charge : `f3641905-00b0-4240-ba50-05ca45bf8abc`

### Personnalisation

Le style peut être modifié via CSS :
```css
/* Exemple de personnalisation */
.quality-level {
    padding: 10px;
    border-radius: 5px;
    font-weight: bold;
}

.excellent { background-color: #4CAF50; }
.good { background-color: #FFC107; }
.moderate { background-color: #FF9800; }
.poor { background-color: #F44336; }
.very-poor { background-color: #9C27B0; }
```

### Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

### Licence

Ce projet est sous licence MIT. 