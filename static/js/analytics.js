// Analytics and visualization functions

// This file contains functions for analyzing ambulance route data
// and displaying insights on the analysis map

// Load and display isochrones
function displayIsochrones(isochroneData) {
    const colors = {
        3: { fill: 'rgba(34, 197, 94, 0.3)', stroke: '#22c55e' },
        5: { fill: 'rgba(251, 191, 36, 0.3)', stroke: '#fbbf24' },
        7: { fill: 'rgba(239, 68, 68, 0.3)', stroke: '#ef4444' }
    };

    isochroneData.forEach(iso => {
        const minutes = iso.minutes;
        L.polygon(iso.geometry, {
            color: colors[minutes].stroke,
            fillColor: colors[minutes].fill,
            fillOpacity: 0.4,
            weight: 2,
            dashArray: '5, 5'
        }).addTo(analysisMap)
            .bindPopup(`<b>${minutes} Minute Zone</b><br>Reachable area from hospital`);
    });
}

// Display route frequency heat map
function displayRouteFrequency(segments) {
    if (!segments || segments.length === 0) {
        return;
    }

    segments.forEach(segment => {
        const frequency = segment.normalized_frequency;
        let color, weight;

        // Color and weight based on frequency
        if (frequency > 0.7) {
            color = '#ef4444'; // Red - high frequency
            weight = 8;
        } else if (frequency > 0.4) {
            color = '#f97316'; // Orange - medium frequency
            weight = 6;
        } else {
            color = '#fbbf24'; // Yellow - low frequency
            weight = 4;
        }

        L.polyline(segment.coordinates, {
            color: color,
            weight: weight,
            opacity: 0.7,
            lineCap: 'round',
            lineJoin: 'round'
        }).addTo(analysisMap)
            .bindPopup(`<b>Route Frequency</b><br>Used ${segment.frequency} time(s)`);
    });
}

// Calculate statistics from trip data
function calculateStatistics(trips) {
    if (!trips || trips.length === 0) {
        return null;
    }

    const totalDistance = trips.reduce((sum, trip) => sum + trip.distance_km, 0);
    const totalDuration = trips.reduce((sum, trip) => sum + trip.duration_minutes, 0);
    const avgDistance = totalDistance / trips.length;
    const avgDuration = totalDuration / trips.length;

    // Find most common pickup location
    const locationCounts = {};
    trips.forEach(trip => {
        locationCounts[trip.pickup_location] = (locationCounts[trip.pickup_location] || 0) + 1;
    });

    const mostCommonLocation = Object.keys(locationCounts).reduce((a, b) =>
        locationCounts[a] > locationCounts[b] ? a : b
    );

    return {
        totalTrips: trips.length,
        totalDistance: totalDistance.toFixed(2),
        totalDuration: Math.round(totalDuration),
        avgDistance: avgDistance.toFixed(2),
        avgDuration: Math.round(avgDuration),
        mostCommonLocation: mostCommonLocation,
        locationCount: locationCounts[mostCommonLocation]
    };
}

// Display statistics on the page
function displayStatistics(stats) {
    if (!stats) return;

    console.log('Trip Statistics:', stats);
    // You can add a statistics panel to the UI if needed
}

// Analyze peak hours from trip data
function analyzePeakHours(trips) {
    const hourCounts = new Array(24).fill(0);

    trips.forEach(trip => {
        const hour = parseInt(trip.time.split(':')[0]);
        hourCounts[hour]++;
    });

    const peakHour = hourCounts.indexOf(Math.max(...hourCounts));
    return {
        peakHour: peakHour,
        peakCount: hourCounts[peakHour],
        hourlyDistribution: hourCounts
    };
}

// Export analytics data
function exportAnalytics(trips) {
    const stats = calculateStatistics(trips);
    const peakHours = analyzePeakHours(trips);

    return {
        statistics: stats,
        peakHours: peakHours,
        generatedAt: new Date().toISOString()
    };
}
