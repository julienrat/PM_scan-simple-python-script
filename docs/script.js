// Configuration des UUIDs BLE
const PMSCAN_SERVICE_UUID = 'f3641900-00b0-4240-ba50-05ca45bf8abc';
const REAL_TIME_DATA_UUID = 'f3641901-00b0-4240-ba50-05ca45bf8abc';
const MEMORY_DATA_UUID = 'f3641902-00b0-4240-ba50-05ca45bf8abc';
const TEMP_HUMID_ALERT_UUID = 'f3641903-00b0-4240-ba50-05ca45bf8abc';
const BATTERY_LEVEL_UUID = 'f3641904-00b0-4240-ba50-05ca45bf8abc';
const BATTERY_CHARGING_UUID = 'f3641905-00b0-4240-ba50-05ca45bf8abc';
const CURRENT_TIME_UUID = 'f3641906-00b0-4240-ba50-05ca45bf8abc';
const ACQUISITION_INTERVAL_UUID = 'f3641907-00b0-4240-ba50-05ca45bf8abc';
const POWER_MODE_UUID = 'f3641908-00b0-4240-ba50-05ca45bf8abc';
const TEMP_HUMID_THRESHOLD_UUID = 'f3641909-00b0-4240-ba50-05ca45bf8abc';
const DISPLAY_SETTINGS_UUID = 'f364190a-00b0-4240-ba50-05ca45bf8abc';
const BATTERY_HEARTBEAT_UUID = 'f364190b-00b0-4240-ba50-05ca45bf8abc';

// Log des UUIDs au démarrage
console.log('UUIDs Bluetooth configurés:');
console.log('Service:', PMSCAN_SERVICE_UUID);
console.log('Données temps réel:', REAL_TIME_DATA_UUID);
console.log('Horloge:', CURRENT_TIME_UUID);
console.log('Niveau batterie:', BATTERY_LEVEL_UUID);
console.log('État charge:', BATTERY_CHARGING_UUID);

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
    if (!data) return;
    
    // Mise à jour des valeurs actuelles
    document.getElementById('state').textContent = `0x${data.state.toString(16).toUpperCase().padStart(2, '0')}`;
    document.getElementById('command').textContent = `0x${data.command.toString(16).toUpperCase().padStart(2, '0')}`;
    document.getElementById('particles').textContent = data.particles_count;
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
    // Vérification de la taille des données
    if (dataView.byteLength !== 20) {
        console.error(`ERREUR: Taille des données invalide: ${dataView.byteLength} bytes (attendu: 20 bytes)`);
        return null;
    }

    // Lecture des données
    const timestamp = dataView.getUint32(0, true);
    const state = dataView.getUint8(4);
    const cmd = dataView.getUint8(5);
    const particles_count = dataView.getUint16(6, true);
    const pm1_0 = dataView.getUint16(8, true);
    const pm2_5 = dataView.getUint16(10, true);
    const pm10_0 = dataView.getUint16(12, true);
    const temp = dataView.getUint16(14, true);
    const humidity = dataView.getUint16(16, true);

    // Vérification des valeurs PM pendant le démarrage
    if (pm1_0 === 0xFFFF || pm2_5 === 0xFFFF || pm10_0 === 0xFFFF) {
        console.log("ATTENTION: Capteur en phase de démarrage, valeurs PM non valides");
        return null;
    }

    // Calcul des valeurs avec division par 10
    const temp_value = temp / 10.0;
    let humidity_value = humidity / 10.0;

    // Vérification des valeurs limites
    if (humidity_value > 100) {
        console.warn(`ATTENTION: Valeur d'humidité anormale détectée: ${humidity_value}%`);
        humidity_value = Math.min(humidity_value, 100);
    }

    if (temp_value < -40 || temp_value > 85) {
        console.warn(`ATTENTION: Température hors limites: ${temp_value}°C`);
    }

    return {
        timestamp: timestamp,
        state: state,
        command: cmd,
        particles_count: particles_count,
        pm1_0: pm1_0 / 10.0,
        pm2_5: pm2_5 / 10.0,
        pm10_0: pm10_0 / 10.0,
        temperature: temp_value,
        humidity: humidity_value
    };
}

// Gestion de la connexion Bluetooth
async function connectToPMScan() {
    try {
        const connectBtn = document.getElementById('connectBtn');
        connectBtn.classList.add('connecting');
        connectBtn.textContent = 'Connexion en cours...';

        bluetoothDevice = await navigator.bluetooth.requestDevice({
            filters: [{ services: [PMSCAN_SERVICE_UUID] }]
        });

        const server = await bluetoothDevice.gatt.connect();
        const service = await server.getPrimaryService(PMSCAN_SERVICE_UUID);
        
        // Configuration des notifications pour les données temps réel
        const characteristic = await service.getCharacteristic(REAL_TIME_DATA_UUID);
        await characteristic.startNotifications();
        characteristic.addEventListener('characteristicvaluechanged', (event) => {
            const data = parseRealTimeData(event.target.value);
            updateUI(data);
        });

        // Configuration des notifications pour la batterie
        const batteryLevelChar = await service.getCharacteristic(BATTERY_LEVEL_UUID);
        await batteryLevelChar.startNotifications();
        batteryLevelChar.addEventListener('characteristicvaluechanged', (event) => {
            const value = event.target.value.getUint8(0);
            document.getElementById('batteryLevel').textContent = value;
            updateBatteryIcon(value);
        });

        // Lecture initiale du niveau de batterie
        const batteryLevel = await batteryLevelChar.readValue();
        const batteryValue = batteryLevel.getUint8(0);
        document.getElementById('batteryLevel').textContent = batteryValue;
        updateBatteryIcon(batteryValue);

        // Configuration des notifications pour l'état de charge
        const batteryChargingChar = await service.getCharacteristic(BATTERY_CHARGING_UUID);
        await batteryChargingChar.startNotifications();
        batteryChargingChar.addEventListener('characteristicvaluechanged', (event) => {
            const value = event.target.value.getUint8(0);
            updateChargingStatus(value);
        });

        // Lecture initiale de l'état de charge
        const chargingState = await batteryChargingChar.readValue();
        updateChargingStatus(chargingState.getUint8(0));

        // Envoi du timestamp actuel
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

        // Gestion de la déconnexion
        bluetoothDevice.addEventListener('gattserverdisconnected', onDisconnected);

    } catch (error) {
        console.error('Erreur de connexion:', error);
        onDisconnected();
    }
}

function updateBatteryIcon(level) {
    const batteryIcon = document.getElementById('batteryIcon');
    if (level >= 75) {
        batteryIcon.className = 'bi bi-battery-full';
    } else if (level >= 50) {
        batteryIcon.className = 'bi bi-battery-half';
    } else if (level >= 25) {
        batteryIcon.className = 'bi bi-battery-low';
    } else {
        batteryIcon.className = 'bi bi-battery';
    }
}

function updateChargingStatus(state) {
    const chargingStatus = document.getElementById('chargingStatus');
    const batteryIcon = document.getElementById('batteryIcon');
    
    switch (state) {
        case 0:
            chargingStatus.textContent = 'Non branché';
            batteryIcon.classList.remove('text-success', 'text-warning');
            break;
        case 1:
            chargingStatus.textContent = 'Pré-charge';
            batteryIcon.classList.add('text-warning');
            batteryIcon.classList.remove('text-success');
            break;
        case 2:
            chargingStatus.textContent = 'En charge';
            batteryIcon.classList.add('text-success');
            batteryIcon.classList.remove('text-warning');
            break;
        case 3:
            chargingStatus.textContent = 'Chargé';
            batteryIcon.classList.add('text-success');
            batteryIcon.classList.remove('text-warning');
            break;
        default:
            chargingStatus.textContent = 'Inconnu';
            batteryIcon.classList.remove('text-success', 'text-warning');
    }
}

// Gestion de la déconnexion
function onDisconnected() {
    const connectBtn = document.getElementById('connectBtn');
    connectBtn.textContent = 'Connecter PMScan';
    connectBtn.classList.remove('connecting', 'btn-danger');
    connectBtn.classList.add('btn-primary');
    
    document.getElementById('connectionStatus').textContent = 'Déconnecté';
    document.getElementById('deviceInfo').classList.add('d-none');
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    
    document.getElementById('connectBtn').addEventListener('click', async () => {
        if (!bluetoothDevice || !bluetoothDevice.gatt.connected) {
            await connectToPMScan();
        } else {
            await bluetoothDevice.gatt.disconnect();
        }
    });
}); 