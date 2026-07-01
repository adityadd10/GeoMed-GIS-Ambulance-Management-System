/**
 * GeoMed Map Core
 * Reusable map component for Dashboard and Analytics
 * Supports:
 * - ambulances
 * - requests
 * - hotspots
 * - optional IITB buildings GeoJSON overlay
 * - optional campus locations layer
 */

class GeoMedMap {

    constructor(containerId) {

        this.map = L.map(containerId).setView([19.1309507, 72.9146062], 15);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            maxZoom: 19
        }).addTo(this.map);

        this.icons = {

            hospital: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            }),

            ambulanceAvailable: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            }),

            ambulanceBusy: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            }),

            patient: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            }),

            campusPOI: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            })

        };

        this.ambLayer = L.layerGroup().addTo(this.map);
        this.reqLayer = L.layerGroup().addTo(this.map);
        this.hotspotLayer = L.layerGroup().addTo(this.map);
        this.campusLayer = L.layerGroup().addTo(this.map);

        this.roadLayer = L.geoJSON(null, {
            style: {
                color: '#f59e0b',
                weight: 3,
                opacity: 0.75
            },
            onEachFeature: (feature, layer) => {
                layer.bindPopup('<b>IITB Internal Road</b>');

            }
        }).addTo(this.map);

        this.buildingLayer = L.geoJSON(null, {

            pointToLayer: (feature, latlng) => {
                const props = feature.properties || {};
                const hasAccess = props.Ambulance_access === true || props.Ambulance_access === 'true';
                return L.circlemarker(latlng, {
                    radius: hasAccess ? 6 : 5,
                    color: hasAccess ? '#16a34a' : '#64748b',
                    fillColor: hasAccess ? '#22c55e' : '#94a3b8',
                    fillOpacity: 0.9,
                    weight: 2
                });
            },

            onEachFeature: (feature, layer) => {
                const props = feature.properties || {};
                const access = props.Ambulance_access ? 'Yes' : 'No';
                layer.bindPopup(`<b>${props.name || 'IITB Location'}</b><br>Ambulance Access: ${access}`);
            }

        }).addTo(this.map);

        L.marker([19.1309507, 72.9146062], { icon: this.icons.hospital })
            .bindPopup("<b>IITB Hospital</b><br>Base Location")
            .addTo(this.map);
    }

    updateAmbulances(ambulances) {

        this.ambLayer.clearLayers();

        ambulances.forEach(amb => {

            const icon = amb.status === 'available'
                ? this.icons.ambulanceAvailable
                : this.icons.ambulanceBusy;

            if (amb.current_lat && amb.current_lon) {

                L.marker([amb.current_lat, amb.current_lon], { icon: icon })
                    .bindPopup(`<b>${amb.vehicle_number}</b><br>Status: ${amb.status}`)
                    .addTo(this.ambLayer);

            }

        });

    }

    updateRequests(requests) {

        this.reqLayer.clearLayers();

        requests.forEach(req => {

            if (req.latitude && req.longitude) {

                L.marker([req.latitude, req.longitude], {
                    icon: this.icons.patient
                })
                    .bindPopup(`<b>Request #${req.id}</b><br>${req.pickup_location}<br>${req.emergency_type}`)
                    .addTo(this.reqLayer);

            }

        });

    }

    updateHotspots(hotspots) {

        this.hotspotLayer.clearLayers();

        hotspots.forEach(hs => {

            L.circle([hs.lat, hs.lon], {
                color: 'red',
                fillColor: '#f03',
                fillOpacity: hs.intensity * 0.5,
                radius: hs.radius_meters
            })
                .bindPopup(`<b>Hotspot:</b> ${hs.name}`)
                .addTo(this.hotspotLayer);

        });

    } loadCampusLocations() {

        fetch('/api/gis/campus-locations')
            .then(r => r.json())
            .then(data => {

                this.campusLayer.clearLayers();

                data.forEach(loc => {

                    L.circleMarker([loc.display_lat, loc.display_lon], {
                        radius: 5,
                        color: loc.has_override ? '#7c3aed' : '#0f766e',
                        fillColor: loc.has_override ? '#a78bfa' : '#14b8a6',
                        fillOpacity: 0.9,
                        weight: 1
                    })
                        .bindPopup(`
                        <b>${loc.name}</b><br>
                        Display: ${loc.display_lat.toFixed(6)}, ${loc.display_lon.toFixed(6)}<br>
                        Route: ${loc.route_lat.toFixed(6)}, ${loc.route_lon.toFixed(6)}<br>
                        Override: ${loc.has_override ? 'Yes' : 'No'}
                    `)
                        .addTo(this.campusLayer);

                });

            })
            .catch(err => console.warn('Campus locations not loaded:', err));

    }

    loadBuildingsOverlay() {

        fetch('/api/gis/buildings-overlay')
            .then(r => r.json())
            .then(meta => {

                if (!meta.geojson_url) return;

                return fetch(meta.geojson_url);

            })
            .then(r => {

                if (!r || !r.ok) return null;

                return r.json();

            })
            .then(geojson => {

                if (!geojson) return;

                this.buildingLayer.clearLayers();
                this.buildingLayer.addData(geojson);

            })
            .catch(err => {

                console.warn(
                    'Buildings overlay not loaded (add static/data/iitb_buildings.geojson later):',
                    err
                );

            });

    }

    loadRoadsOverlay() {
        fetch('/api/gis/roads-overlay')
            .then(r => r.json())
            .then(meta => {
                if (!meta.geojson_url) return null;
                return fetch(meta.geojson_url);
            })
            .then(r => {
                if (!r || !r.ok) return null;
                return r.json();
            })
            .then(geojson => {
                if (!geojson) return;

                this.roadLayer.clearLayers();
                this.roadLayer.addData(geojson);
            })
            .catch(err => {
                console.warn('Road overlay not loaded (add static/data/iitb_road_geojson.geojson later):', err);
            });
    }

}