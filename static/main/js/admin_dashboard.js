// JavaScript for Admin Dashboard

document.addEventListener('DOMContentLoaded', function() {
    const readingDetailsModal = document.getElementById('readingDetailsModal');
    let latestSensorData = null; // Variable to store the latest fetched data

    // Function to fetch the latest sensor data via AJAX
    function fetchLatestSensorData() {
        fetch('/api/latest-readings-json/')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.sensor_data) {
                    latestSensorData = data.sensor_data;
                    updateDashboardCards(latestSensorData);
                    // Optional: Update latest timestamp display
                    if (data.latest_timestamp) {
                        // You might have an element to display this, e.g., a small text below the cards
                        console.log('Latest data timestamp:', data.latest_timestamp);
                    }
                } else {
                    console.error('Error fetching data:', data.message);
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
            });
    }

    // Function to update the content of the dashboard cards
    function updateDashboardCards(sensorData) {
        // Iterate through the sensorData and update the corresponding card elements
        for (const sensorName in sensorData) {
            const data = sensorData[sensorName];
            // Find the card element using the data-sensor-name attribute
            const cardElement = document.querySelector(`.status-card[data-sensor-name='${sensorName}']`);
            if (cardElement) {
                // Update value
                const valueElement = cardElement.querySelector('.sensor-value');
                if (valueElement) {
                     // Check if data.value is a number before calling toFixed
                     valueElement.textContent = data.value !== null && !isNaN(data.value) ? parseFloat(data.value).toFixed(1) : 'N/A';
                }

                // Update status
                const statusTextElement = cardElement.querySelector('.status-text');
                 if (statusTextElement) {
                     statusTextElement.textContent = `Status: ${data.status}`;
                     // Update status class on the status text element
                     statusTextElement.className = `mb-2 status-text status-${data.status.toLowerCase()}`;
                 }
                 // Update status class on the card itself for border styling
                 // Keep existing classes and only update the status class part
                 const currentClasses = cardElement.className.split(' ').filter(c => !c.startsWith('status-'));
                 cardElement.className = `${currentClasses.join(' ')} status-${data.status.toLowerCase()}`;

                // Update change percent
                const changeTextElement = cardElement.querySelector('.change-text');
                if (changeTextElement) {
                     changeTextElement.innerHTML = `Change: ${getChangeHtml(data.change_percent)}`;
                }
            }
        }
    }

    // Helper function to get the unit (adjust as needed)
    function getUnit(sensorName) {
        switch (sensorName) {
            case 'temperature': return '°C';
            case 'humidity': return '%';
            case 'pressure': return 'hPa';
            case 'gas_resistance': return 'kΩ';
            case 'ammonia': return 'PPM';
            case 'pm1_0':
            case 'pm2_5':
            case 'pm10': return 'μg/m³';
            default: return '';
        }
    }

    // Helper function to generate HTML for percent change (adjust as needed)
    function getChangeHtml(changePercent) {
        if (changePercent === 'N/A') {
            return 'Change: N/A';
        } else if (changePercent.startsWith('+')) {
            return `<span class="text-success"><i class='bx bx-up-arrow-alt'></i> ${changePercent}</span>`;
        } else if (changePercent.startsWith('-')) {
            // Remove the '-' for display with the danger text color
            return `<span class="text-danger"><i class='bx bx-down-arrow-alt'></i> ${changePercent.slice(1)}</span>`;
        } else {
            return `<span>${changePercent}</span>`;
        }
    }

    // Event listener for modal show
    if (readingDetailsModal) {
        readingDetailsModal.addEventListener('show.bs.modal', function (event) {
            // Populate modal body with latestSensorData
            const modalBody = readingDetailsModal.querySelector('.modal-body');
            const modalTitle = readingDetailsModal.querySelector('.modal-title');
            modalTitle.textContent = 'Sensor Reading Details'; // Or include timestamp if available

            let modalContent = '';
            if (latestSensorData) {
                 // Add timestamp to modal
                 // Use the latest_timestamp from the fetched data
                 const latestTimestamp = latestSensorData.latest_timestamp; // Get the timestamp from the fetched data
                 if (latestTimestamp) {
                      modalContent += `<p><strong>Timestamp:</strong> ${new Date(latestTimestamp).toLocaleString()}</p>`;
                 }

                for (const sensorName in latestSensorData) {
                    const data = latestSensorData[sensorName];
                    // Exclude latest_timestamp and other non-sensor fields if any
                     if (typeof data === 'object' && data !== null && data.hasOwnProperty('value')) {
                         modalContent += `<p><strong>${data.display_name}:</strong> ${data.value !== null ? data.value.toFixed(1) : 'N/A'}${getUnit(sensorName)}
                         `;
                         // Add status and change to the modal content string
                         modalContent += ` - Status: <span class="status-${data.status.toLowerCase()}">${data.status}</span>`;
                         if (data.change_percent !== 'N/A') {
                              modalContent += ` (${getChangeHtml(data.change_percent)} change)`;
                         }
                         modalContent += `</p>`;

                         // Add text explanation based on status
                         let explanation = 'Data is within normal range.';
                         if (data.status === 'Warning') {
                              explanation = 'Reading is approaching a threshold. Monitor closely.';
                         } else if (data.status === 'Alert') {
                              explanation = 'Reading is outside the safe threshold. Immediate attention required!';
                         }
                         modalContent += `<p><small>${explanation}</small></p>`;
                     }
                }
            } else {
                modalContent = '<p>No sensor details available.</p>';
            }
            modalBody.innerHTML = modalContent;
        });
    }

    // Fetch data on page load
    fetchLatestSensorData();

    // Fetch data periodically (e.g., every 30 seconds)
    setInterval(fetchLatestSensorData, 30000);
}); 