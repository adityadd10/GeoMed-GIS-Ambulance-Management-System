// Global variables
let routeMap, analysisMap;
let hospitalCoords = [19.1309507, 72.9146062];
let ambulanceMarker;
let currentRoute = null;
let pickupMarker = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    initializeMaps();
    loadCurrentOdometer();
    loadLocations();
    setCurrentDateTime();
    setupEventListeners();
});

// Initialize Leaflet maps
function initializeMaps() {
    // Route Map
    routeMap = L.map('routeMap').setView(hospitalCoords, 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(routeMap);

    // Add hospital marker
    L.marker(hospitalCoords, {
        icon: L.divIcon({
            className: 'hospital-marker',
            html: '<i class="fas fa-hospital" style="color: #10b981; font-size: 24px;"></i>',
            iconSize: [30, 30]
        })
    }).addTo(routeMap).bindPopup('<b>IITB Hospital</b>');

    // Analysis Map
    analysisMap = L.map('analysisMap').setView(hospitalCoords, 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(analysisMap);

    // Add hospital marker to analysis map
    L.marker(hospitalCoords, {
        icon: L.divIcon({
            className: 'hospital-marker',
            html: '<i class="fas fa-hospital" style="color: #10b981; font-size: 24px;"></i>',
            iconSize: [30, 30]
        })
    }).addTo(analysisMap).bindPopup('<b>IITB Hospital</b>');

    // Load analytics data
    loadIsochrones();
    loadRouteFrequency();
}

// Load current odometer reading
async function loadCurrentOdometer() {
    try {
        const response = await fetch('/api/get-current-odometer');
        const data = await response.json();
        document.getElementById('kmReading').value = data.odometer.toFixed(3);
    } catch (error) {
        console.error('Error loading odometer:', error);
        document.getElementById('kmReading').value = '205539.000';
    }
}

// Load campus locations
async function loadLocations() {
    try {
        const response = await fetch('/api/get-locations');
        const data = await response.json();

        const select = document.getElementById('fromLocation');
        data.locations.forEach(location => {
            const option = document.createElement('option');
            option.value = JSON.stringify({
                name: location.name,
                lat: location.lat,
                lon: location.lon
            });
            option.textContent = location.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading locations:', error);
    }
}

// Set current date and time
function setCurrentDateTime() {
    const now = new Date();

    // Set date
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    document.getElementById('date').value = `${year}-${month}-${day}`;

    // Set time
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    document.getElementById('time').value = `${hours}:${minutes}`;
}

// Setup event listeners
function setupEventListeners() {
    // Form submission
    document.getElementById('tripForm').addEventListener('submit', handleFormSubmit);

    // Export CSV
    document.getElementById('exportBtn').addEventListener('click', exportCSV);
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const locationData = JSON.parse(formData.get('fromLocation'));

    const tripData = {
        date: formData.get('date'),
        time: formData.get('time'),
        pickup_location: locationData.name,
        pickup_lat: locationData.lat,
        pickup_lon: locationData.lon,
        patient_name: formData.get('patientName'),
        driver_name: formData.get('driverName'),
        purpose: formData.get('purpose'),
        notes: formData.get('notes')
    };

    // Show loading
    document.getElementById('loadingOverlay').classList.add('active');

    try {
        const response = await fetch('/api/submit-trip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tripData)
        });

        const data = await response.json();

        if (data.success) {
            // Display route on map
            displayRoute(data, locationData);

            // Update trip summary
            updateTripSummary(data);

            // Update odometer
            loadCurrentOdometer();

            // Reload analytics
            loadRouteFrequency();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error submitting trip:', error);
        alert('Error submitting trip. Please check your API key in config.py');
    } finally {
        document.getElementById('loadingOverlay').classList.remove('active');
    }
}

// Display route on map
function displayRoute(data, locationData) {
    // Clear previous route
    clearRoute();

    // Add pickup location marker
    pickupMarker = L.marker([locationData.lat, locationData.lon], {
        icon: L.divIcon({
            className: 'pickup-marker',
            html: '<i class="fas fa-map-marker-alt" style="color: #ef4444; font-size: 24px;"></i>',
            iconSize: [30, 30]
        })
    }).addTo(routeMap).bindPopup(`<b>${locationData.name}</b>`);

    // Combine route geometries
    const route1Coords = data.route1.geometry;
    const route2Coords = data.route2.geometry;
    const allCoords = [...route1Coords, ...route2Coords];

    // Draw route
    currentRoute = L.polyline(allCoords, {
        color: '#3b82f6',
        weight: 4,
        opacity: 0.7
    }).addTo(routeMap);

    // Fit map to route
    routeMap.fitBounds(currentRoute.getBounds(), { padding: [50, 50] });

    // Animate ambulance
    animateAmbulance(allCoords);
}

// Clear route from map (but keep ambulance at hospital)
function clearRoute() {
    if (currentRoute) {
        routeMap.removeLayer(currentRoute);
        currentRoute = null;
    }
    if (pickupMarker) {
        routeMap.removeLayer(pickupMarker);
        pickupMarker = null;
    }
    // Keep ambulance marker at hospital - don't remove it
}

// Format duration as min:sec
function formatDuration(minutes) {
    const mins = Math.floor(minutes);
    const secs = Math.round((minutes - mins) * 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Animate ambulance marker along route
function animateAmbulance(coords) {
    let index = 0;

    // Remove old ambulance marker if exists
    if (ambulanceMarker) {
        routeMap.removeLayer(ambulanceMarker);
    }

    // Create ambulance marker
    ambulanceMarker = L.marker(coords[0], {
        icon: L.divIcon({
            className: 'ambulance-marker',
            html: '<i class="fas fa-ambulance" style="color: #ffffff; font-size: 20px; background: #3b82f6; padding: 8px; border-radius: 50%;"></i>',
            iconSize: [40, 40]
        })
    }).addTo(routeMap);

    // Animate (slower speed: 100ms per point instead of 50ms)
    const interval = setInterval(() => {
        if (index < coords.length - 1) {
            index++;
            ambulanceMarker.setLatLng(coords[index]);
        } else {
            clearInterval(interval);
            // Move ambulance back to hospital and clear route after 2 seconds
            setTimeout(() => {
                ambulanceMarker.setLatLng(hospitalCoords);
                clearRoute();
                console.log('Trip completed - ambulance returned to hospital');
            }, 2000);
        }
    }, 200); // Slower animation speed (200ms per point - 4x slower than original)
}

// Update trip summary
function updateTripSummary(data) {
    document.getElementById('summaryDistance').textContent = data.total_distance.toFixed(2) + ' km';
    document.getElementById('summaryDuration').textContent = formatDuration(data.total_duration);
    document.getElementById('summaryDeparture').textContent = data.trip.departure_time;
    document.getElementById('summaryArrival').textContent = data.trip.arrival_time;
    document.getElementById('summaryOdometer').textContent =
        data.trip.km_reading_start.toFixed(3) + ' → ' + data.trip.km_reading_end.toFixed(3) + ' km';

    document.getElementById('tripSummary').style.display = 'block';
}

// Export CSV
async function exportCSV() {
    try {
        window.location.href = '/api/export-csv';
    } catch (error) {
        console.error('Error exporting CSV:', error);
        alert('Error exporting CSV');
    }
}

// Load isochrones (called from analytics.js)
async function loadIsochrones() {
    try {
        const response = await fetch('/api/get-isochrones');
        const data = await response.json();

        if (data.success) {
            const colors = {
                3: 'rgba(34, 197, 94, 0.3)',
                5: 'rgba(251, 191, 36, 0.3)',
                7: 'rgba(239, 68, 68, 0.3)'
            };

            data.isochrones.forEach(iso => {
                L.polygon(iso.geometry, {
                    color: colors[iso.minutes],
                    fillColor: colors[iso.minutes],
                    fillOpacity: 0.4,
                    weight: 2
                }).addTo(analysisMap).bindPopup(`${iso.minutes} minute zone`);
            });
        } else {
            // Silently fail - isochrones are optional analytics feature
            console.log('Isochrones not available:', data.error);
        }
    } catch (error) {
        // Silently fail - isochrones are optional analytics feature
        console.log('Could not load isochrones (this is normal if ORS API is unavailable)');
    }
}

// Load route frequency (called from analytics.js)
async function loadRouteFrequency() {
    try {
        const response = await fetch('/api/get-route-frequency');
        const data = await response.json();

        if (data.success && data.segments.length > 0) {
            data.segments.forEach(segment => {
                const frequency = segment.normalized_frequency;
                let color;

                // Color based on frequency
                if (frequency > 0.7) {
                    color = '#ef4444'; // Red - high frequency
                } else if (frequency > 0.4) {
                    color = '#f97316'; // Orange - medium frequency
                } else {
                    color = '#fbbf24'; // Yellow - low frequency
                }

                L.polyline(segment.coordinates, {
                    color: color,
                    weight: 6,
                    opacity: 0.7
                }).addTo(analysisMap).bindPopup(`Used ${segment.frequency} times`);
            });
        }
    } catch (error) {
        console.error('Error loading route frequency:', error);
    }
}
