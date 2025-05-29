// Function to format sensor value with appropriate unit
function formatSensorValue(sensorName, value) {
    let unit = '';
    switch(sensorName) {
        case 'temperature':
            unit = '°C';
            break;
        case 'humidity':
            unit = '%';
            break;
        case 'pressure':
            unit = ' hPa';
            break;
        case 'gas_resistance':
            unit = ' kΩ';
            break;
        case 'ammonia':
            unit = ' PPM';
            break;
        case 'pm1_0':
        case 'pm2_5':
        case 'pm10':
            unit = ' μg/m³';
            break;
    }
    return value.toFixed(1) + unit;
}

// Function to update modal content
function updateModalContent(sensorName, data) {
    const modalSensorData = document.getElementById('modalSensorData');
    const modalTimestamp = document.getElementById('modalTimestamp');
    if (!modalSensorData || !modalTimestamp) return;

    // Update timestamp
    modalTimestamp.textContent = new Date(data.timestamp).toLocaleString();

    let html = `
        <p><strong>${data.display_name}:</strong> ${formatSensorValue(sensorName, data.value)}
            ${data.change_percent !== 'N/A' ? `(${data.change_percent} change)` : ''}
            - Status: <span class="status-${data.status.toLowerCase()}">${data.status}</span>
        </p>`;
    
    if (data.status === 'Warning') {
        html += '<p><small>Reading is approaching a threshold. Monitor closely.</small></p>';
    } else if (data.status === 'Alert') {
        html += '<p><small>Reading is outside the safe threshold. Immediate attention required!</small></p>';
    } else {
        html += '<p><small>Data is within normal range.</small></p>';
    }
    
    modalSensorData.innerHTML = html;
}

// Function to update card content
function updateCardContent(sensorName, data) {
    const card = document.querySelector(`[data-sensor-name="${sensorName}"]`);
    if (!card) return;

    // Update status class
    card.className = `card h-100 border-0 shadow-sm hover-card status-card status-${data.status.toLowerCase()}`;
    
    // Update status text
    const statusElement = card.querySelector('.status-text');
    if (statusElement) {
        statusElement.textContent = `Status: ${data.status}`;
        statusElement.className = `mb-2 status-text status-${data.status.toLowerCase()}`;
    }

    // Update value
    const valueElement = card.querySelector('.sensor-value');
    if (valueElement) {
        valueElement.textContent = formatSensorValue(sensorName, data.value);
    }

    // Update change percentage
    const changeElement = card.querySelector('.change-text');
    if (changeElement) {
        if (data.change_percent !== 'N/A') {
            let changeHtml = 'Change: ';
            if (data.change_percent.startsWith('+')) {
                changeHtml += `<span class="text-success"><i class='bx bx-up-arrow-alt'></i> ${data.change_percent}</span>`;
            } else if (data.change_percent.startsWith('-')) {
                changeHtml += `<span class="text-danger"><i class='bx bx-down-arrow-alt'></i> ${data.change_percent.slice(1)}</span>`;
            } else {
                changeHtml += `<span>${data.change_percent}</span>`;
            }
            changeElement.innerHTML = changeHtml;
        } else {
            changeElement.innerHTML = 'Change: N/A';
        }
    }
}

// Function to fetch latest sensor data
function fetchLatestSensorData() {
    fetch('/api/latest-sensor-data/')
        .then(response => response.json())
        .then(data => {
            // Update timestamp
            const timestampElement = document.getElementById('latestTimestamp');
            if (timestampElement) {
                timestampElement.textContent = new Date(data.timestamp).toLocaleString();
            }

            // Update each sensor's data
            Object.entries(data.sensor_data).forEach(([sensorName, sensorData]) => {
                updateCardContent(sensorName, sensorData);
            });

            // Update modal if it's open
            const modal = document.getElementById('readingDetailsModal');
            if (modal && modal.classList.contains('show')) {
                const activeSensorName = modal.getAttribute('data-active-sensor');
                if (activeSensorName && data.sensor_data[activeSensorName]) {
                    updateModalContent(activeSensorName, data.sensor_data[activeSensorName]);
                }
            }
        })
        .catch(error => console.error('Error fetching sensor data:', error));
}

// Initialize event listeners when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Set up modal event listeners
    const modal = document.getElementById('readingDetailsModal');
    if (modal) {
        // When modal is shown
        modal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const sensorName = button.getAttribute('data-sensor-name');
            modal.setAttribute('data-active-sensor', sensorName);
            
            // Get initial data from the current state
            const sensorData = window.sensorData[sensorName];
            if (sensorData) {
                updateModalContent(sensorName, sensorData);
            }
        });

        // When modal is hidden
        modal.addEventListener('hidden.bs.modal', function() {
            modal.removeAttribute('data-active-sensor');
        });
    }

    // Start periodic updates
    fetchLatestSensorData(); // Initial fetch
    setInterval(fetchLatestSensorData, 5000); // Update every 5 seconds
}); 