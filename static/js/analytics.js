
let analyticsMapCore = null;

let analyticsTripLayers = [];

let analyticsFrequencyLayers = [];

let analyticsZoneLayers = [];



/* ----------------------------- 

   Utility helpers 

------------------------------ */



async function fetchJSON(url) {
    const response = await fetch(url);
    return response.json();
}


function formatMinutes(value) {
    if (value === null || value === undefined || isNaN(value)) return '--';
    return `${Number(value).toFixed(1)} min`;
}


function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function criticalityClass(name) {
    const value = (name || 'unknown').toLowerCase();
    if (value === 'critical') return 'critical';
    if (value === 'high') return 'high';
    if (value === 'moderate') return 'moderate';
    if (value === 'low') return 'low';
    return 'unknown';
}

function renderTopIncidentsList(containerId, incidents, limit = 5) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!incidents || !incidents.length) {
        container.innerHTML = `<div class="chart-empty">No incidents</div>`;
        return;
    }

    container.innerHTML = incidents.slice(0, limit).map((item, index) => {
        const criticality = item.criticality_name || 'Unknown';
        const cls = criticalityClass(criticality);
        return `
        <div class="compact-list-item">
            <strong>${index + 1}.${item.incident_name}</strong>
            <span class="criticality-badge ${cls}">
            ${criticality}${item.criticality_level ? 'L' + item.criticality_level :
                ''
            }   
            </span>
            <div class = "text-xs text-gray">${item.count} case(s)</div>
        </div>
        `;
    }).join('');

}

function renderTopLocationsList(containerId, locations, limit = 3) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!locations || !locations.length) {
        container.innerHTML = `<div class="chart-empty">No locations</div>`;
        return;
    }

    container.innerHTML = locations.slice(0, limit).map((item, index) => {
        return `
        <div class="compact-list-item">
            <strong>${index + 1}.${item.location}</strong>
            <div class = "text-xs text-gray">${item.count} visits</div>
        </div>
        `;
    }).join('');
}

function renderBarChart(containerId, data, labelKey, valueKey, color = '#2563eb', limit = null) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';

    if (!data || !data.length) {
        container.innerHTML = `<div class="chart-empty">No data available</div>`;
        return;
    }



    let rows = [...data];
    if (limit) rows = rows.slice(0, limit);

    const maxValue = Math.max(...rows.map(r => Number(r[valueKey] || 0)), 1);
    const chart = document.createElement('div');
    chart.className = 'simple-bar-chart';



    rows.forEach(row => {
        const value = Number(row[valueKey] || 0);
        const height = Math.max(8, (value / maxValue) * 180);

        const col = document.createElement('div');
        col.className = 'simple-bar-column';

        const valueDiv = document.createElement('div');
        valueDiv.className = 'simple-bar-value';
        valueDiv.textContent = value;

        const bar = document.createElement('div');
        bar.className = 'simple-bar';
        bar.style.height = `${height}px`;
        bar.style.background = color;

        const label = document.createElement('div');
        label.className = 'simple-bar-label';
        label.textContent = row[labelKey];

        col.appendChild(valueDiv);
        col.appendChild(bar);
        col.appendChild(label);

        chart.appendChild(col);
    });



    container.appendChild(chart);

}



/* ----------------------------- 

   KPI Loaders 

------------------------------ */

async function loadSummaryKPIs() {

    try {

        const data = await fetchJSON('/api/analytics/summary');



        setText('kpi-trips-today', data.trips_today ?? 0);

        setText('kpi-trips-month', data.trips_this_month ?? 0);

        setText('kpi-avg-eta', formatMinutes(data.avg_eta_min));

        setText('kpi-avg-actual', formatMinutes(data.avg_actual_time_min));


        if (data.peak_hour !== null && data.peak_hour !== undefined) {

            setText('kpi-peak-hour', `${String(data.peak_hour).padStart(2, '0')}:00`);
            setText('kpi-peak-hour-count', `${data.peak_hour_count ?? 0}trip(s)`);

        } else {

            setText('kpi-peak-hour', '--');
            setText('kpi-peak-hour-count', '--');

        }

        renderTopLocationsList('kpi-top-locations', data.top_locations || [], 3);

    } catch (err) {

        console.error('Failed to load overview KPIs:', err);

    }



}

async function loadTopIncidents() {
    const data = await fetchJSON('/api/analytics/top-incidents');
    renderTopIncidentsList('kpi-top-incidents', data, 5);
    renderBarChart('chart-top-incidents', data, 'incident_name', 'count', '#f97316', 10)
}

async function loadTripsByHourChart() {
    const data = await fetchJSON('/api/analytics/trips-by-hour');
    const formatted = data.map(item => ({
        label: `${String(item.hour).padStart(2, '0')}`,
        count: item.count
    }))
    renderBarChart('chart-trips-by-hour', formatted, 'label', 'count', '#0ea5e9', 24);
}

async function loadTripsByDayCurrentMonthChart() {
    const data = await fetchJSON('/api/analytics/trips-by-day-current-month');
    renderBarChart('chart-trips-by-day-month', data, 'date', 'count', '#2563eb', 31);
}

function cleanTripRoutes() {
    analyticsTripLayers.forEach(layer => {
        try {
            analyticsMapCore.map.removeLayer(layer);
        }
        catch (err) { }
    });
    analyticsTripLayers = [];
}

function cleanFrequencyRoutes() {
    analyticsFrequencyLayers.forEach(layer => {
        try {
            analyticsMapCore.map.removeLayer(layer);
        }
        catch (err) { }
    });
    analyticsFrequencyLayers = [];
}

function cleanZoneLayers() {
    analyticsZoneLayers.forEach(layer => {
        try {
            analyticsMapCore.map.removeLayer(layer);
        }
        catch (err) { }
    });
    analyticsZoneLayers = [];
}

function cleanMapOverlays() {
    cleanTripRoutes();
    cleanFrequencyRoutes();
    cleanZoneLayers();
}

function cleaMapOverlays() {
    cleanMapOverlays();
}

async function loadTrips() {
    cleanTripRoutes();
    const data = await fetchJSON('/api/trips');

    let bounds = [];
    data.forEach(trip => {
        if (!trip.route_geometry) return;

        try {
            let geom = trip.route_geometry;

            if (typeof geom === 'string') {
                geom = JSON.parse(geom);
            }

            if (Array.isArray(geom) && geom.length > 1) {
                const line = L.polyline(geom, { color: '#2563eb', weight: 3, opacity: 0.65 }).bindPopup(`
                <b>${trip.pickup_location || 'Trip'}</b><br>
                Distance: ${(trip.distance_km || 0).toFixed(2)}km<br>
                Actual Time: ${(trip.duration_minutes || 0).toFixed(1)}mins
                `).addTo(analyticsMapCore.map);
                analyticsTripLayers.push(line);
                bounds = bounds.concat(geom);
            }
        } catch (e) {
            console.warn("Skipping invalid route geometry:", trip.id, e);
        }
    });

    if (bounds.length > 0) {
        analyticsMapCore.map.fitBounds(bounds, { padding: [25, 25] });
    }
}

async function loadRouteFrequencyLayer() {
    cleanFrequencyRoutes();
    const data = await fetchJSON('/api/analytics/route-frequency');

    if (!data || !data.length) {
        alert('No route frequency data available');
        return;
    }
    let bounds = [];

    data.forEach(segment => {
        let color = "#fbbf24";
        let weight = 4;

        if (segment.color === 'red') {
            color = '#ef4444';
            weight = 8;
        } else if (segment.color === 'orange') {
            color = '#f97316';
            weight = 6;
        }

        const line = L.polyline(segment.coordinates, { color: color, weight: weight, opacity: 0.75, lineCap: 'round', lineJoin: 'round' }).bindPopup(`
            <b>Frequently Visited Road Segment</b><br>
            Used ${segment.frequency} time(s)`).addTo(analyticsMapCore.map);
        analyticsFrequencyLayers.push(line);
        bounds = bounds.concat(segment.coordinates);
    });

    if (bounds.length > 0) {
        analyticsMapCore.map.fitBounds(bounds, { padding: [25, 25] });
    }
}

async function loadEmergencyZones() {
    cleanZoneLayers();

    const data = await fetchJSON('/api/analytics/emergency-zones');

    if (!data || !data.length) {
        alert('No emergency zones data available');
        return;
    }

    let bounds = [];

    data.forEach(zone => {
        let color = '#16a34a';

        if (zone.color === 'red') {
            color = '#ef4444';
        } else if (zone.color === 'orange') {
            color = '#f97316'
        }

        const circle = L.circle([zone.lat, zone.lon], {
            radius: zone.radius,
            color: color,
            fillColor: color,
            fillOpacity: 0.25,
            weight: 2
        }).bindPopup(`
            <b>${zone.location}</b><br>
            ${zone.risk})<br>
            Patients/Requests: ${zone.count}`).addTo(analyticsMapCore.map);
        analyticsZoneLayers.push(circle);
        bounds.push([zone.lat, zone.lon]);
    });

    if (bounds.length > 0) {
        analyticsMapCore.map.fitBounds(bounds, { padding: [25, 25] });
    }
}

document.addEventListener('DOMContentLoaded', async () => {

    analyticsMapCore = new GeoMedMap('analytics-map');

    if (typeof analyticsMapCore.loadBuildingsOverlay === 'function') {
        analyticsMapCore.loadBuildingsOverlay();
    }

    if (typeof analyticsMapCore.loadRoadOverlay === 'function') {
        analyticsMapCore.loadRoadOverlay();
    }

    await Promise.all([
        loadSummaryKPIs(),
        loadTopIncidents(),
        loadTripsByHourChart(),
        loadTripsByDayCurrentMonthChart()
    ]);

});
