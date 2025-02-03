// Configuration des UUIDs BLE
const PMSCAN_SERVICE_UUID = 'f3641900-00b0-4240-ba50-05ca45bf8abc';
const REAL_TIME_DATA_UUID = 'f3641901-00b0-4240-ba50-05ca45bf8abc';
const CURRENT_TIME_UUID = 'f3641906-00b0-4240-ba50-05ca45bf8abc';

// Variables globales
let bluetoothDevice;
let pmChart;
const maxDataPoints = 50;
const datasets = {
    pm1: [],
    pm25: [],
    pm10: [],
    labels: []
};

// Vérification de la disponibilité du Bluetooth
function isWebBluetoothAvailable() {
    if (!navigator.bluetooth) {
        console.error('Web Bluetooth API non disponible');
        alert('Votre navigateur ne supporte pas le Web Bluetooth. Veuillez utiliser Chrome, Edge ou Opera.');
        return false;
    }
    return true;
}

// Initialisation du graphique
function initChart() {
    const ctx = document.getElementById('pmChart').getContext('2d');
    pmChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: datasets.labels,
            datasets: [
                {
                    label: 'PM1.0',
                    data: datasets.pm1,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },
                {
                    label: 'PM2.5',
                    data: datasets.pm25,
                    borderColor: 'rgb(255, 159, 64)',
                    tension: 0.1
                },
                {
                    label: 'PM10.0',
                    data: datasets.pm10,
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            animation: {
                duration: 0
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Concentration (μg/m³)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Temps'
                    }
                }
            }
        }
    });
}

// Mise à jour de l'interface utilisateur
function updateUI(data) {
    try {
        // Mise à jour des valeurs actuelles
        document.getElementById('pm1').textContent = data.pm1_0.toFixed(1);
        document.getElementById('pm25').textContent = data.pm2_5.toFixed(1);
        document.getElementById('pm10').textContent = data.pm10_0.toFixed(1);
        document.getElementById('temp').textContent = data.temperature.toFixed(1);
        document.getElementById('humidity').textContent = data.humidity.toFixed(1);

        // Mise à jour du graphique
        const now = new Date().toLocaleTimeString();
        datasets.labels.push(now);
        datasets.pm1.push(data.pm1_0);
        datasets.pm25.push(data.pm2_5);
        datasets.pm10.push(data.pm10_0);

        // Limite le nombre de points affichés
        if (datasets.labels.length > maxDataPoints) {
            datasets.labels.shift();
            datasets.pm1.shift();
            datasets.pm25.shift();
            datasets.pm10.shift();
        }

        pmChart.update();

        // Mise à jour de l'indicateur de qualité
        updateQualityIndicator(data.pm10_0);
    } catch (error) {
        console.error('Erreur lors de la mise à jour de l\'interface:', error);
    }
}

// Mise à jour de l'indicateur de qualité de l'air
function updateQualityIndicator(pm10) {
    const indicator = document.getElementById('qualityIndicator');
    let quality, className;

    if (pm10 < 10) {
        quality = 'Excellente';
        className = 'excellent';
    } else if (pm10 < 30) {
        quality = 'Bonne';
        className = 'good';
    } else if (pm10 < 50) {
        quality = 'Moyenne';
        className = 'moderate';
    } else if (pm10 < 80) {
        quality = 'Mauvaise';
        className = 'poor';
    } else {
        quality = 'Très mauvaise';
        className = 'very-poor';
    }

    indicator.textContent = `Qualité de l'air : ${quality}`;
    indicator.className = `quality-level ${className}`;
}

// Parsage des données reçues
function parseRealTimeData(dataView) {
    try {
        return {
            timestamp: dataView.getUint32(0, true),
            pm1_0: dataView.getUint16(8, true) / 10.0,
            pm2_5: dataView.getUint16(10, true) / 10.0,
            pm10_0: dataView.getUint16(12, true) / 10.0,
            temperature: dataView.getUint16(14, true) / 10.0,
            humidity: dataView.getUint16(16, true) / 10.0
        };
    } catch (error) {
        console.error('Erreur lors du parsage des données:', error);
        throw error;
    }
}

// Gestion de la connexion Bluetooth
async function connectToPMScan() {
    if (!isWebBluetoothAvailable()) {
        return;
    }

    try {
        const connectBtn = document.getElementById('connectBtn');
        connectBtn.classList.add('connecting');
        connectBtn.textContent = 'Connexion en cours...';
        connectBtn.disabled = true;

        console.log('Demande de connexion Bluetooth...');
        bluetoothDevice = await navigator.bluetooth.requestDevice({
            filters: [{ 
                services: [PMSCAN_SERVICE_UUID],
                // Ajout du nom optionnel pour faciliter l'identification
                namePrefix: 'PMScan'
            }]
        });

        console.log('Connexion au serveur GATT...');
        const server = await bluetoothDevice.gatt.connect();
        
        console.log('Recherche du service...');
        const service = await server.getPrimaryService(PMSCAN_SERVICE_UUID);
        
        console.log('Configuration des notifications...');
        const characteristic = await service.getCharacteristic(REAL_TIME_DATA_UUID);
        await characteristic.startNotifications();
        
        characteristic.addEventListener('characteristicvaluechanged', (event) => {
            try {
                const data = parseRealTimeData(event.target.value);
                updateUI(data);
            } catch (error) {
                console.error('Erreur lors de la réception des données:', error);
            }
        });

        console.log('Envoi du timestamp...');
        const timeChar = await service.getCharacteristic(CURRENT_TIME_UUID);
        const timestamp = Math.floor(Date.now() / 1000);
        const buffer = new ArrayBuffer(4);
        new DataView(buffer).setUint32(0, timestamp, true);
        await timeChar.writeValue(buffer);

        // Mise à jour de l'interface
        document.getElementById('deviceInfo').classList.remove('d-none');
        document.getElementById('connectionStatus').textContent = 'Connecté';
        connectBtn.textContent = 'Déconnecter';
        connectBtn.classList.remove('connecting');
        connectBtn.classList.add('btn-danger');
        connectBtn.disabled = false;

        // Gestion de la déconnexion
        bluetoothDevice.addEventListener('gattserverdisconnected', onDisconnected);

    } catch (error) {
        console.error('Erreur de connexion:', error);
        alert(`Erreur de connexion: ${error.message}`);
        onDisconnected();
    }
}

// Gestion de la déconnexion
function onDisconnected() {
    const connectBtn = document.getElementById('connectBtn');
    connectBtn.textContent = 'Connecter PMScan';
    connectBtn.classList.remove('connecting', 'btn-danger');
    connectBtn.classList.add('btn-primary');
    connectBtn.disabled = false;
    
    document.getElementById('connectionStatus').textContent = 'Déconnecté';
    document.getElementById('deviceInfo').classList.add('d-none');

    console.log('Déconnecté du PMScan');
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initialisation de l\'application...');
    
    // Vérification initiale du Bluetooth
    isWebBluetoothAvailable();
    
    // Initialisation du graphique
    initChart();
    
    // Configuration du bouton de connexion
    const connectBtn = document.getElementById('connectBtn');
    connectBtn.addEventListener('click', async () => {
        try {
            if (!bluetoothDevice || !bluetoothDevice.gatt.connected) {
                await connectToPMScan();
            } else {
                console.log('Déconnexion...');
                await bluetoothDevice.gatt.disconnect();
            }
        } catch (error) {
            console.error('Erreur lors de la gestion de la connexion:', error);
            onDisconnected();
        }
    });

    console.log('Application initialisée');
}); 