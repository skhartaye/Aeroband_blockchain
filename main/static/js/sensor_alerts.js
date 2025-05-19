// Sensor Alert Suggestions
const sensorSuggestions = {
    temperature: {
        warning: {
            high: [
                "Ensure proper ventilation in the area",
                "Check if any heating equipment is malfunctioning",
                "Move temperature-sensitive items to a cooler location",
                "Consider turning on air conditioning or fans"
            ],
            low: [
                "Check for drafts or open windows in the area",
                "Ensure heating systems are functioning properly",
                "Protect sensitive equipment that may be affected by low temperatures",
                "Consider using supplemental heating if necessary"
            ]
        },
        alert: {
            high: [
                "IMMEDIATE ACTION REQUIRED: Extreme temperature detected",
                "Evacuate sensitive electronic equipment from the area",
                "Check for fire hazards or overheating equipment",
                "Implement emergency cooling procedures if available",
                "Contact facility management immediately"
            ],
            low: [
                "IMMEDIATE ACTION REQUIRED: Dangerously low temperature detected",
                "Check for frozen pipes or at-risk water systems",
                "Protect any water-based systems from freezing damage",
                "Increase heating immediately if possible",
                "Monitor sensitive equipment that may be damaged by extreme cold"
            ]
        }
    },
    humidity: {
        warning: {
            high: [
                "Check for water leaks or sources of moisture",
                "Use a dehumidifier if available",
                "Ensure proper ventilation in the area",
                "Monitor for mold development in humid conditions"
            ],
            low: [
                "Consider using a humidifier to increase moisture levels",
                "Be aware of increased static electricity risk",
                "Monitor wooden items for potential cracking or damage",
                "Keep plants and sensitive materials properly hydrated"
            ]
        },
        alert: {
            high: [
                "IMMEDIATE ACTION REQUIRED: Extreme humidity detected",
                "Check for water intrusion, leaks, or flooding",
                "Power off sensitive electronic equipment that may be affected",
                "Deploy dehumidifiers at maximum capacity if available",
                "Monitor for rapid mold growth which may occur in these conditions"
            ],
            low: [
                "IMMEDIATE ACTION REQUIRED: Extremely low humidity detected",
                "Be aware of increased fire risk in these dry conditions",
                "Take precautions against static electricity around sensitive equipment",
                "Consider temporarily relocating sensitive wooden items or instruments",
                "Deploy humidifiers if available"
            ]
        }
    },
    pressure: {
        warning: {
            high: [
                "Monitor weather conditions as high pressure may indicate weather changes",
                "Be aware of potential issues with pressure-sensitive equipment",
                "Ensure pressure-sensitive processes are monitored carefully"
            ],
            low: [
                "Be prepared for possible weather changes or storms",
                "Check calibration of pressure-sensitive equipment",
                "Monitor pressure-dependent systems for proper operation"
            ]
        },
        alert: {
            high: [
                "IMMEDIATE ACTION REQUIRED: Abnormally high pressure detected",
                "Verify pressure sensor calibration if readings seem unusual",
                "Monitor for pressure-induced stress on sealed systems or containers",
                "Be prepared for significant weather pattern changes"
            ],
            low: [
                "IMMEDIATE ACTION REQUIRED: Abnormally low pressure detected",
                "Be prepared for possible severe weather developments",
                "Check pressure-sensitive equipment for proper functioning",
                "Verify pressure sensor calibration if readings seem unusual"
            ]
        }
    },
    gas_resistance: {
        warning: {
            high: [
                "Possible air quality issue detected",
                "Ensure proper ventilation in the area",
                "Consider using air purifiers if available"
            ],
            low: [
                "Possible volatile organic compounds (VOCs) detected",
                "Increase ventilation in the area",
                "Check for chemical spills or new sources of pollution"
            ]
        },
        alert: {
            high: [
                "IMMEDIATE ACTION REQUIRED: Significant air quality issue detected",
                "Increase ventilation immediately",
                "Consider evacuating sensitive individuals from the area",
                "Check for gas leaks or chemical releases",
                "Use respiratory protection if entering the area"
            ],
            low: [
                "IMMEDIATE ACTION REQUIRED: High levels of contaminants detected",
                "Evacuate the area if odors are detected or if experiencing symptoms",
                "Maximize ventilation immediately",
                "Identify and isolate potential sources of contamination",
                "Consider professional air quality assessment"
            ]
        }
    },
    ammonia: {
        warning: {
            high: [
                "Possible ammonia presence detected",
                "Ensure adequate ventilation in the area",
                "Check known ammonia sources for possible leaks",
                "Be alert for characteristic ammonia odor"
            ]
        },
        alert: {
            high: [
                "IMMEDIATE ACTION REQUIRED: High ammonia levels detected",
                "Evacuate non-essential personnel from the area",
                "Use appropriate respiratory protection if entering the area",
                "Check ammonia-containing systems for leaks",
                "Open windows and maximize ventilation if safe to do so",
                "Contact emergency services if levels continue to rise"
            ]
        }
    },
    pm1_0: {
        warning: {
            high: [
                "Fine particulate matter detected at elevated levels",
                "Consider using HEPA air filtration if available",
                "Reduce activities that generate dust or aerosols",
                "Monitor respiratory symptoms in sensitive individuals"
            ]
        },
        alert: {
            high: [
                "IMMEDIATE ACTION REQUIRED: High fine particulate matter detected",
                "Use HEPA air purifiers at maximum capacity if available",
                "Keep windows closed if outdoor air quality is poor",
                "Consider wearing appropriate masks if entering the area",
                "Sensitive individuals (with asthma, COPD, etc.) should avoid the area",
                "Identify and eliminate sources of particles if possible"
            ]
        }
    },
    pm2_5: {
        warning: {
            high: [
                "Elevated PM2.5 levels detected - these particles can penetrate deep into lungs",
                "Use HEPA air filtration if available",
                "Limit outdoor air intake if outdoor pollution is the source",
                "Consider wearing appropriate masks in affected areas"
            ]
        },
        alert: {
            high: [
                "IMMEDIATE ACTION REQUIRED: Dangerous PM2.5 levels detected",
                "Sensitive individuals should evacuate the area",
                "Use high-efficiency air purifiers at maximum capacity",
                "Wear N95 or better masks if entering the area is necessary",
                "Identify and control the source of particulates if possible",
                "Keep all windows and external doors closed if outdoor air is the source"
            ]
        }
    },
    pm10: {
        warning: {
            high: [
                "Elevated coarse particulate matter detected",
                "Consider using air filtration systems",
                "Reduce activities that generate dust",
                "Increase cleaning of surfaces to reduce re-suspension of particles"
            ]
        },
        alert: {
            high: [
                "IMMEDIATE ACTION REQUIRED: High levels of coarse particles detected",
                "Use air filtration systems at maximum capacity",
                "Wear appropriate masks if entering affected areas",
                "Avoid activities that disturb dust or create more particulates",
                "Consider professional cleaning services if issue persists",
                "Keep windows and doors closed if outdoor air is the source"
            ]
        }
    }
};

// Get suggestions based on sensor type, status, and value
function getSensorSuggestions(sensorType, status, value) {
    if (status === 'Normal' || !sensorSuggestions[sensorType]) {
        return null;
    }
    
    if (!sensorSuggestions[sensorType][status.toLowerCase()]) {
        return null;
    }
    
    // Determine if this is a high or low condition
    let condition;
    
    // Define thresholds
    const thresholds = {
        'temperature': { 'high': 30, 'low': 0 },
        'humidity': { 'high': 70, 'low': 20 },
        'pressure': { 'high': 1020, 'low': 1000 },
        'gas_resistance': { 'high': 200, 'low': 50 },
        'ammonia': { 'high': 1, 'low': null },
        'pm1_0': { 'high': 20, 'low': null },
        'pm2_5': { 'high': 30, 'low': null },
        'pm10': { 'high': 50, 'low': null }
    };
    
    if (sensorType in thresholds) {
        if (thresholds[sensorType].high !== null && value > thresholds[sensorType].high) {
            condition = 'high';
        } else if (thresholds[sensorType].low !== null && value < thresholds[sensorType].low) {
            condition = 'low';
        } else {
            condition = 'high'; // Default if we can't determine
        }
    } else {
        condition = 'high'; // Default for unknown sensors
    }
    
    // Return suggestions if available for this condition
    return sensorSuggestions[sensorType][status.toLowerCase()][condition] || null;
}

// Format suggestions into HTML
function formatSuggestions(suggestions) {
    if (!suggestions || suggestions.length === 0) {
        return '<p>No specific recommendations available.</p>';
    }
    
    let html = '<ul class="suggestion-list">';
    
    suggestions.forEach(suggestion => {
        html += `<li class="suggestion-item">${suggestion}</li>`;
    });
    
    html += '</ul>';
    
    return html;
}

// Update alerts list with current sensor status
function updateAlertsList(sensorData) {
    const alertsList = document.getElementById('alerts-list');
    if (!alertsList) return;
    
    let alertsHtml = '';
    let hasAlerts = false;
    
    // First show Alerts, then Warnings
    for (const severity of ['Alert', 'Warning']) {
        for (const [sensorId, data] of Object.entries(sensorData)) {
            if (data.status === severity) {
                hasAlerts = true;
                
                const suggestions = getSensorSuggestions(sensorId, data.status, data.value);
                const suggestionsHtml = formatSuggestions(suggestions);
                
                alertsHtml += `
                    <div class="alert-card status-${data.status.toLowerCase()}">
                        <div class="alert-header">
                            <span class="alert-sensor">${data.display_name}</span>
                            <span class="alert-value">${data.value} ${getSensorUnit(sensorId)}</span>
                        </div>
                        <div class="alert-status">${data.status}</div>
                        <div class="alert-suggestions">
                            <h4>Recommended Actions:</h4>
                            ${suggestionsHtml}
                        </div>
                    </div>
                `;
            }
        }
    }
    
    if (!hasAlerts) {
        alertsHtml = `
            <div class="no-alerts">
                <i class="material-icons">check_circle</i>
                <p>All sensors reporting normal conditions.</p>
            </div>
        `;
    }
    
    alertsList.innerHTML = alertsHtml;
}

// Get appropriate unit for sensor
function getSensorUnit(sensorId) {
    const units = {
        'temperature': '°C',
        'humidity': '%',
        'pressure': 'hPa',
        'gas_resistance': 'Ohms',
        'ammonia': 'ppm',
        'pm1_0': 'μg/m³',
        'pm2_5': 'μg/m³',
        'pm10': 'μg/m³'
    };
    
    return units[sensorId] || '';
}

// Update alerts badge with count of current alerts and warnings
function updateAlertsBadge(sensorData) {
    const alertsBadge = document.getElementById('alerts-badge');
    if (!alertsBadge) return;
    
    let alertCount = 0;
    
    for (const data of Object.values(sensorData)) {
        if (data.status === 'Alert' || data.status === 'Warning') {
            alertCount++;
        }
    }
    
    alertsBadge.textContent = alertCount;
    
    if (alertCount > 0) {
        alertsBadge.style.display = 'flex';  // Use flex instead of block for better centering
    } else {
        alertsBadge.style.display = 'none';
    }
} 