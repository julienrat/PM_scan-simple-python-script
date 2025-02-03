# 🌐 PMScan - Interface Web

## 📝 Description
L'interface web PMScan permet de visualiser en temps réel les données de votre capteur PMScan directement dans votre navigateur. Elle utilise la technologie Web Bluetooth pour une connexion sans installation et propose une interface moderne et intuitive.

## ✨ Fonctionnalités
- 📊 Graphiques en temps réel
- 🎨 Interface responsive et moderne
- 🔄 Mise à jour automatique des données
- 🌈 Indicateur visuel de qualité de l'air
- 📱 Compatible mobile et desktop
- 🔌 Connexion directe via Web Bluetooth

## 💻 Prérequis
- Un navigateur compatible Web Bluetooth :
  - ✅ Chrome (Desktop & Android)
  - ✅ Edge
  - ✅ Opera
  - ❌ Firefox (Web Bluetooth non supporté)
  - ❌ Safari (Web Bluetooth non supporté)
- Un capteur PMScan
- Une connexion Bluetooth

## 🚀 Utilisation

### En ligne
1. Accédez à [https://julienrat.github.io/PM_scan-simple-python-script/](https://julienrat.github.io/PM_scan-simple-python-script/)
2. Cliquez sur "Connecter PMScan"
3. Sélectionnez votre appareil
4. Les données s'afficheront automatiquement

### En local
1. Clonez le dépôt :
```bash
git clone https://github.com/julienrat/PM_scan-simple-python-script.git
```

2. Ouvrez `index.html` dans un navigateur compatible
   - Note : Pour le développement local, utilisez un serveur HTTPS
   - Exemple avec Python :
     ```bash
     python -m http.server 8000
     ```

## 📊 Interface utilisateur

### Panneau principal
- Valeurs en temps réel :
  - PM1.0, PM2.5, PM10.0 (μg/m³)
  - Température (°C)
  - Humidité (%)
- Indicateur de qualité de l'air
- État de la connexion

### Graphiques
- Historique des particules :
  - PM1.0 (bleu)
  - PM2.5 (orange)
  - PM10.0 (rouge)
- Échelle automatique
- 50 derniers points de mesure

### Indicateurs
- 🟢 Excellente qualité (PM10 < 10 μg/m³)
- 🟡 Bonne qualité (PM10 10-30 μg/m³)
- 🟠 Qualité moyenne (PM10 30-50 μg/m³)
- 🔴 Mauvaise qualité (PM10 50-80 μg/m³)
- 🟣 Très mauvaise qualité (PM10 > 80 μg/m³)

## 🔧 Personnalisation

### Styles CSS
Le fichier `style.css` permet de personnaliser :
```css
/* Couleurs des graphiques */
--chart-pm1: rgb(75, 192, 192);
--chart-pm25: rgb(255, 159, 64);
--chart-pm10: rgb(255, 99, 132);

/* Indicateurs de qualité */
.quality-level.excellent { background-color: #4CAF50; }
.quality-level.good { background-color: #FFEB3B; }
.quality-level.moderate { background-color: #FF9800; }
.quality-level.poor { background-color: #F44336; }
.quality-level.very-poor { background-color: #9C27B0; }
```

### Configuration des graphiques
Dans `script.js` :
```javascript
const maxDataPoints = 50;  // Nombre de points affichés
const updateInterval = 1000;  // Intervalle de mise à jour (ms)

// Options du graphique
const chartOptions = {
    responsive: true,
    animation: { duration: 0 },
    scales: {
        y: { beginAtZero: true }
    }
};
```

## 🐛 Dépannage

### Problèmes courants
1. Connexion impossible :
   - Vérifiez la compatibilité du navigateur
   - Activez le Bluetooth
   - Utilisez HTTPS en local

2. Graphiques figés :
   - Rafraîchissez la page
   - Vérifiez la console pour les erreurs
   - Reconnectez le PMScan

3. Données manquantes :
   - Vérifiez la portée Bluetooth
   - Assurez-vous que le PMScan est allumé
   - Vérifiez la connexion dans les paramètres Bluetooth

### Console de débogage
Pour accéder aux logs :
1. Ouvrez les outils de développement (F12)
2. Sélectionnez l'onglet "Console"
3. Filtrez par "PMScan" pour voir les messages spécifiques

## 🔒 Sécurité
- L'interface utilise uniquement HTTPS
- Aucune donnée n'est stockée en ligne
- Les données restent locales au navigateur
- La connexion Bluetooth est sécurisée

## 📱 Version mobile
- Interface responsive
- Optimisée pour les écrans tactiles
- Gestion des orientations portrait/paysage
- Boutons adaptés au tactile

## 🎨 Thèmes
L'interface supporte les thèmes clair et sombre :
- Détection automatique du thème système
- Variables CSS pour une personnalisation facile
- Transitions fluides entre les thèmes

## 📚 Ressources
- [Web Bluetooth API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Bluetooth_API)
- [Chart.js](https://www.chartjs.org/)
- [Bootstrap](https://getbootstrap.com/) 