# 🌐 Interface Web PMScan

## 📝 Description
Cette interface web permet de visualiser en temps réel les données du capteur PMScan via Web Bluetooth. Elle offre une visualisation graphique des concentrations de particules et des indicateurs de qualité de l'air.

## 🔧 Fonctionnalités
- 📱 Connexion Bluetooth directe depuis le navigateur
- 📊 Graphique en temps réel des concentrations PM1.0, PM2.5 et PM10.0
- 🌡️ Affichage de la température et de l'humidité
- 🎨 Interface responsive et moderne
- 🔄 Mise à jour automatique des données
- 🌈 Indicateur visuel de la qualité de l'air

## 💻 Prérequis
- Un navigateur web moderne supportant Web Bluetooth
  - Chrome (recommandé)
  - Edge
  - Opera
- Un appareil PMScan
- Une connexion Bluetooth

## 🚀 Utilisation
1. Ouvrez le fichier `index.html` dans un navigateur compatible
2. Allumez votre capteur PMScan
3. Cliquez sur le bouton "Connecter PMScan"
4. Sélectionnez votre appareil dans la liste
5. Les données s'afficheront automatiquement

## ⚠️ Compatibilité
- ✅ Chrome Desktop (Windows, macOS, Linux)
- ✅ Chrome Android
- ✅ Edge
- ✅ Opera
- ❌ Firefox (Web Bluetooth non supporté)
- ❌ Safari (Web Bluetooth non supporté)

## 🔧 Structure des fichiers
- `index.html` : Page principale de l'interface
- `style.css` : Styles et mise en page
- `script.js` : Logique de connexion et traitement des données

## 📚 Technologies utilisées
- HTML5
- CSS3
- JavaScript (ES6+)
- Chart.js pour les graphiques
- Bootstrap 5 pour l'interface
- Web Bluetooth API

## 🐛 Dépannage
- Si la connexion échoue :
  1. Vérifiez que le Bluetooth est activé
  2. Rafraîchissez la page
  3. Redémarrez le capteur PMScan
- Si le graphique ne s'affiche pas :
  1. Vérifiez la console du navigateur
  2. Assurez-vous que JavaScript est activé

## 🔒 Sécurité
L'interface utilise exclusivement HTTPS pour la connexion Web Bluetooth.
Aucune donnée n'est stockée en dehors de votre navigateur.

## 📱 Version mobile
L'interface est entièrement responsive et s'adapte aux écrans mobiles.
Utilisez Chrome pour Android pour une expérience optimale. 