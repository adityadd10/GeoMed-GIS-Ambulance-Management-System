
let analyticsMapCore = null; 

let analyticsTripLayers = []; 

let analyticsFrequencyLayers = []; 

let analyticsHotspotLayers = []; 

 

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

 

async function loadOverviewKPIs() { 

    try { 

        const data = await fetchJSON('/api/analytics/overview'); 

 

        setText('kpi-total-trips', data.total_trips ?? 0); 

        setText('kpi-total-distance', `${(data.total_distance_km ?? 0).toFixed(2)} km`); 

        setText('kpi-avg-eta', formatMinutes(data.avg_eta_min)); 

        setText('kpi-avg-actual', formatMinutes(data.avg_actual_time_min)); 

        setText('kpi-avg-response', formatMinutes(data.avg_response_time_min)); 

 

        if (data.peak_hour !== null && data.peak_hour !== undefined) { 

            setText('kpi-peak-hour', `${String(data.peak_hour).padStart(2, '0')}:00`); 

        } else { 

            setText('kpi-peak-hour', '--'); 

        } 

    } catch (err) { 

        console.error('Failed to load overview KPIs:', err); 

    } 

} 

 

async function loadHighlights() { 

    try { 

        const data = await fetchJSON('/api/analytics/highlights'); 

 

        setText('highlight-completed-today', data.completed_today ?? 0); 

 

        setText('highlight-top-category', data.top_category?.name ?? '--'); 

        setText('highlight-top-category-count', `${data.top_category?.count ?? 0} cases`); 

 

        setText('highlight-top-hostel', data.top_hostel?.name ?? '--'); 

        setText('highlight-top-hostel-count', `${data.top_hostel?.count ?? 0} incidents`); 

 

        setText('highlight-busiest-ambulance', data.busiest_ambulance?.name ?? '--'); 

        setText('highlight-busiest-ambulance-count', `${data.busiest_ambulance?.count ?? 0} trips`); 

    } catch (err) { 

        console.error('Failed to load highlights:', err); 

    } 

} 

 

async function loadTripsByDayChart() { 

    try { 

        const data = await fetchJSON('/api/analytics/trips-by-day'); 

        renderBarChart('chart-trips-by-day', data, 'date', 'count', '#2563eb', 14); 

    } catch (err) { 

        console.error('Failed to load trips-by-day:', err); 

    } 

} 

 

async function loadTripsByHourChart() { 

    try { 

        const data = await fetchJSON('/api/analytics/trips-by-hour'); 

        const chartData = data.map(d => ({ 

            hour_label: `${String(d.hour).padStart(2, '0')}`, 

            count: d.count 

        })); 

        renderBarChart('chart-trips-by-hour', chartData, 'hour_label', 'count', '#0ea5e9', 24); 

    } catch (err) { 

        console.error('Failed to load trips-by-hour:', err); 

    } 

} 

 

async function loadCategoryDistributionChart() { 

    try { 

        const data = await fetchJSON('/api/analytics/category-distribution'); 

        renderBarChart('chart-category-distribution', data, 'category', 'count', '#f97316', 10); 

    } catch (err) { 

        console.error('Failed to load category distribution:', err); 

    } 

} 

 

async function loadHostelDistributionChart() { 

    try { 

        const data = await fetchJSON('/api/analytics/hostel-distribution'); 

        renderBarChart('chart-hostel-distribution', data, 'hostel', 'count', '#10b981', 10); 

    } catch (err) { 

        console.error('Failed to load hostel distribution:', err); 

    } 

} 

 

async function loadZoneDistributionChart() { 

    try { 

        const data = await fetchJSON('/api/analytics/zone-distribution'); 

        renderBarChart('chart-zone-distribution', data, 'zone', 'count', '#8b5cf6', 10); 

    } catch (err) { 

        console.error('Failed to load zone distribution:', err); 

    } 

} 

 

async function loadBusiestAmbulancesChart() { 

    try { 

        const data = await fetchJSON('/api/analytics/busiest-ambulances'); 

        renderBarChart('chart-busiest-ambulances', data, 'ambulance', 'count', '#ef4444', 10); 

    } catch (err) { 

        console.error('Failed to load busiest ambulances:', err); 

    } 

} 

 

async function loadPerformanceSummary() { 

    try { 

        const data = await fetchJSON('/api/analytics/performance'); 

        const container = document.getElementById('performance-summary'); 

 

        if (!container) return; 

 

        container.innerHTML = ` 

            <div class="performance-card"> 

                <div class="performance-label">Completed Trips</div> 

                <div class="performance-value">${data.completed_trip_count ?? 0}</div> 

            </div> 

            <div class="performance-card"> 

                <div class="performance-label">Avg ETA</div> 

                <div class="performance-value">${formatMinutes(data.avg_eta_min)}</div> 

            </div> 

            <div class="performance-card"> 

                <div class="performance-label">Avg Actual Time</div> 

                <div class="performance-value">${formatMinutes(data.avg_actual_time_min)}</div> 

            </div> 

            <div class="performance-card"> 

                <div class="performance-label">Avg ETA Gap</div> 

                <div class="performance-value">${formatMinutes(data.avg_eta_gap_min)}</div> 

            </div> 

            <div class="performance-card"> 

                <div class="performance-label">On-Time Rate</div> 

                <div class="performance-value">${(data.on_time_rate_percent ?? 0).toFixed(1)}%</div> 

            </div> 

        `; 

    } catch (err) { 

        console.error('Failed to load performance summary:', err); 

    } 

} 

 

/* ----------------------------- 

   Forecast 

------------------------------ */ 

 

async function loadForecast() { 

    try { 

        const data = await fetchJSON('/api/ml/forecast'); 

        const container = document.getElementById('forecast-container'); 

 

        if (!container) return; 

 

        if (data.error) { 

            container.innerHTML = `<div class="chart-empty">${data.error}</div>`; 

            return; 

        } 

 

        let html = '<div class="forecast-grid">'; 

        data.forEach(d => { 

            const dateObj = new Date(d.date); 

            const day = dateObj.toLocaleDateString('en-US', { weekday: 'short' }); 

            html += ` 

                <div class="text-center p-3 border rounded ${d.is_weekend ? 'bg-gray-50' : ''}"> 

                    <div class="text-sm text-gray font-bold">${day}</div> 

                    <div class="text-xl font-bold text-blue-600 my-2">${d.expected_requests}</div> 

                    <div class="text-xs text-gray">Calls</div> 

                </div> 

            `; 

        }); 

        html += '</div>'; 

        container.innerHTML = html; 

    } catch (err) { 

        console.error('Failed to load forecast:', err); 

    } 

} 

 

/* ----------------------------- 

   Map actions 

------------------------------ */ 

 

function clearTripRoutes() { 

    analyticsTripLayers.forEach(layer => { 

        try { 

            analyticsMapCore.map.removeLayer(layer); 

        } catch (e) {} 

    }); 

    analyticsTripLayers = []; 

} 

 

function clearFrequencyRoutes() { 

    analyticsFrequencyLayers.forEach(layer => { 

        try { 

            analyticsMapCore.map.removeLayer(layer); 

        } catch (e) {} 

    }); 

    analyticsFrequencyLayers = []; 

} 

 

function clearMapOverlays() { 

    clearTripRoutes(); 

    clearFrequencyRoutes(); 

 

    if (analyticsMapCore && analyticsMapCore.hotspotLayer) { 

        analyticsMapCore.hotspotLayer.clearLayers(); 

    } 

} 

 

async function loadTrips() { 

    try { 

        clearTripRoutes(); 

 

        const data = await fetchJSON('/api/trips'); 

        if (data.error) { 

            alert(data.error); 

            return; 

        } 

 

        let drawnCount = 0; 

        let bounds = []; 

 

        data.forEach(trip => { 

            if (!trip.route_geometry) return; 

 

            try { 

                let geom = trip.route_geometry; 

                if (typeof geom === 'string') { 

                    geom = JSON.parse(geom); 

                } 

 

                if (Array.isArray(geom) && geom.length > 1) { 

                    const line = L.polyline(geom, { 

                        color: '#2563eb', 

                        weight: 3, 

                        opacity: 0.65 

                    }).bindPopup(` 

                        <b>${trip.pickup_location || 'Trip'}</b><br> 

                        Patient: ${trip.patient_name || '-'}<br> 

                        Distance: ${(trip.distance_km || 0).toFixed(2)} km<br> 

                        Actual Time: ${(trip.duration_minutes || 0).toFixed(1)} min 

                    `).addTo(analyticsMapCore.map); 

 

                    analyticsTripLayers.push(line); 

                    bounds = bounds.concat(geom); 

                    drawnCount++; 

                } 

            } catch (e) { 

                console.warn('Skipping invalid trip geometry:', trip.id, e); 

            } 

        }); 

 

        if (drawnCount === 0) { 

            alert('No trips with valid route geometry were found.'); 

        } else if (bounds.length > 0) { 

            analyticsMapCore.map.fitBounds(bounds, { padding: [30, 30] }); 

        } 

    } catch (err) { 

        console.error('Failed to load trips:', err); 

        alert('Failed to load trips.'); 

    } 

} 

 

async function loadRouteFrequencyLayer() { 

    try { 

        clearFrequencyRoutes(); 

 

        const data = await fetchJSON('/api/analytics/route-frequency'); 

        if (!data || !data.length) { 

            alert('No route frequency data available.'); 

            return; 

        } 

 

        let bounds = []; 

 

        data.forEach(segment => { 

            const freq = segment.normalized_frequency || 0; 

            let color = '#fbbf24'; 

            let weight = 4; 

 

            if (freq > 0.7) { 

                color = '#ef4444'; 

                weight = 8; 

            } else if (freq > 0.4) { 

                color = '#f97316'; 

                weight = 6; 

            } 

 

            const line = L.polyline(segment.coordinates, { 

                color: color, 

                weight: weight, 

                opacity: 0.7, 

                lineCap: 'round', 

                lineJoin: 'round' 

            }).bindPopup(` 

                <b>Route Segment Frequency</b><br> 

                Used ${segment.frequency} time(s) 

            `).addTo(analyticsMapCore.map); 

 

            analyticsFrequencyLayers.push(line); 

            bounds = bounds.concat(segment.coordinates); 

        }); 

 

        if (bounds.length > 0) { 

            analyticsMapCore.map.fitBounds(bounds, { padding: [30, 30] }); 

        } 

    } catch (err) { 

        console.error('Failed to load route frequency layer:', err); 

    } 

} 

 

async function loadHotspots() { 

    try { 

        const data = await fetchJSON('/api/ml/hotspots'); 

        if (data.error) { 

            alert(data.error); 

            return; 

        } 

        analyticsMapCore.updateHotspots(data); 

    } catch (err) { 

        console.error('Failed to load hotspots:', err); 

    } 

} 

 

function loadCampusOverlay() { 

    if (!analyticsMapCore) return; 

 

    if (typeof analyticsMapCore.loadCampusLocations === 'function') { 

        analyticsMapCore.loadCampusLocations(); 

    } 

 

    if (typeof analyticsMapCore.loadBuildingsOverlay === 'function') { 

        analyticsMapCore.loadBuildingsOverlay(); 

    } 

} 

 

/* ----------------------------- 

   Boot 

------------------------------ */ 

 

document.addEventListener('DOMContentLoaded', async () => { 

    analyticsMapCore = new GeoMedMap('analytics-map'); 

 

    if (typeof analyticsMapCore.loadBuildingsOverlay === 'function') { 

        analyticsMapCore.loadBuildingsOverlay(); 

    } 

 

    if (typeof analyticsMapCore.loadCampusLocations === 'function') { 

        analyticsMapCore.loadCampusLocations(); 

    } 

 

    await Promise.all([ 

        loadOverviewKPIs(), 

        loadHighlights(), 

        loadTripsByDayChart(), 

        loadTripsByHourChart(), 

        loadCategoryDistributionChart(), 

        loadHostelDistributionChart(), 

        loadZoneDistributionChart(), 

        loadBusiestAmbulancesChart(), 

        loadPerformanceSummary(), 

        loadForecast() 

    ]); 

}); 

 