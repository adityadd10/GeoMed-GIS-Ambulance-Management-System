"""
GeoMed Analytics API

Phase 5: Advanced analytics + route frequency intelligence

"""


from collections import Counter, defaultdict

from datetime import datetime, date

from flask import jsonify, render_template

from flask_login import login_required

from extensions import db

from models import Trip, Task, AmbulanceTrip, PatientRequest

from . import analytics_bp

import json


def _parse_legacy_datetime(date_str, time_str):

    if not date_str:

        return None

    candidates = [

        "%Y-%m-%d %H:%M",

        "%Y-%m-%d %H:%M:%S",

        "%d-%m-%Y %H:%M",

        "%d/%m/%Y %H:%M",

        "%d/%m/%Y %H:%M:%S",

    ]

    combined = f"{date_str} {time_str or '00:00'}".strip()

    for fmt in candidates:

        try:

            return datetime.strptime(combined, fmt)

        except Exception:

            continue

    return None


def _safe_avg(values):

    values = [v for v in values if v is not None]

    if not values:

        return 0

    return round(sum(values) / len(values), 2)



def _safe_parse_geometry(geom):

    if not geom:

        return []

    try:

        if isinstance(geom, str):

            parsed = json.loads(geom)

        else:

            parsed = geom

        if isinstance(parsed, list):

            return parsed

    except Exception:

        pass

    return []



def _segment_key(p1, p2, precision=4):

    """

    Creates a direction-agnostic segment key by rounding both endpoints.

    """

    a = (round(p1[0], precision), round(p1[1], precision))

    b = (round(p2[0], precision), round(p2[1], precision))

    return tuple(sorted([a, b]))

def _get_new_trips_pairs():
    return (
        db.session.query(Task, Trip)
        .join(Trip, Trip.task_id == Task.id)
        .all()
    )


@analytics_bp.route('/analytics')

@login_required

def index():

    return render_template('analytics.html', page='analytics')


@analytics_bp.route('/api/analytics/summary', methods=['GET'])

@login_required

def analytics_summary():

    today = date.today()
    current_year = today.year
    current_month = today.month

    legacy_trips = AmbulanceTrip.query.all()

    new_trips = Trip.query.all()

    task_trip_pairs = _get_new_trips_pairs()

    trips_today = 0
    trips_this_month = 0
    hour_counter = Counter()

    location_counter = Counter()
    for req in PatientRequest.query.all():
        if req.pickup_location:
            location_counter[req.pickup_location] += 1

    for trip in legacy_trips:
        dt = _parse_legacy_datetime(trip.date, trip.time)
        if dt:
            if dt.date() == today:
                trips_today += 1
            if dt.year == current_year and dt.month == current_month:
                trips_this_month += 1
            hour_counter[dt.hour] += 1
            if trip.pickup_location: location_counter[trip.pickup_location] += 1

    for task, trip in task_trip_pairs:
        dt = trip.created_at
        if trip.created_at:
            if dt:
                if dt.date() == today:
                    trips_today += 1
                if dt.year == current_year and dt.month == current_month:
                    trips_this_month += 1
                hour_counter[dt.hour] += 1
            req = task.request if task else None
            if req and req.pickup_location:
                location_counter[req.pickup_location] += 1
    eta_values = [
        task.estimated_duration_min
        for task, trip in task_trip_pairs
        if task.estimated_duration_min is not None
    ]
    actual_values = [
        trip.duration_minutes
        for task, trip in task_trip_pairs
        if trip.duration_minutes is not None
    ]
    peak_hour = None
    peak_hour_count = 0

    if hour_counter:
        peak_hour, peak_hour_count = hour_counter.most_common(1)[0]
    
    top_location = [
        {
            "location": location,
            "count": count
        }
        for location, count in location_counter.most_common(3)
    ]

    return jsonify({
        "trips_today":trips_today,
        "trips_this_month":trips_this_month,
        "avg_eta_min":_safe_avg(eta_values),
        "avg_actual_time_min":_safe_avg(actual_values),
        "peak_hour":peak_hour,
        "peak_hour_count":peak_hour_count,
        "top_location":top_location,
    })

@analytics_bp.route('/api/analytics/top-incidents',methods=['GET'])
@login_required
def analytics_top_incidents():
    task_trip_pairs = _get_new_trips_pairs()
    counter = Counter()
    meta = {}
    for task, trip in task_trip_pairs:
        req = task.request if task else None
        if req and req.incident_name: 
            incident_name = req.incident_name
            criticality_name = req.criticality_name or "Unknown"
            criticality_level = req.criticality_level
        else:
            incident_name = trip.incident_category or "Unknown"
            criticality_name = None
            criticality_level = None
        counter[incident_name] += 1
        if incident_name not in meta:
            meta[incident_name] = {
                "name": incident_name,
                "criticality_name": criticality_name,
                "criticality_level": criticality_level
            }   

    results = []
    for incident_name, count in counter.most_common():
        item = meta.get(incident_name, {})
        results.append({
            "incident_name": incident_name,
            "count": count,
            "criticality_name": item.get("criticality_name"),
            "criticality_level": item.get("criticality_level")
        })

    return jsonify(results)
        
@analytics_bp.route('/api/analytics/trips-by-hour', methods=['GET'])

@login_required

def analytics_trips_by_hour():

    counter = Counter({h: 0 for h in range(24)})
    legacy_trips = AmbulanceTrip.query.all()
    new_trips = Trip.query.all()
    
    for trip in legacy_trips:
        dt = _parse_legacy_datetime(trip.date, trip.time)
        if dt:
            counter[dt.hour] += 1

    for trip in new_trips:
        if trip.created_at:
            counter[trip.created_at.hour] += 1

    results = [{"hour": hour, "count": counter[hour]} for hour in range(24)]

    return jsonify(results)

@analytics_bp.route('/api/analytics/trips-by-day-current-month', methods=['GET'])
@login_required
def analytics_trips_by_day_current_month():

    today = date.today()
    current_year = today.year
    current_month = today.month
    legacy_trips = AmbulanceTrip.query.all()
    new_trips = Trip.query.all()
    counter = Counter()

    for trip in legacy_trips:
        dt = _parse_legacy_datetime(trip.date, trip.time)
        if dt and dt.year == current_year and dt.month == current_month:
            counter[dt.strftime("%Y-%m-%d")] += 1

    for trip in new_trips:
        dt = trip.created_at
        if dt and dt.year == current_year and dt.month == current_month:
            counter[dt.strftime("%Y-%m-%d")] += 1

    results = [{"date": day, "count": counter[day]} for day in sorted(counter.keys())]
    return jsonify(results)

@analytics_bp.route('/api/analytics/top-locations', methods = ['GET'])
@login_required
def analytics_top_locations():
    counter = Counter()
    legacy_trips = AmbulanceTrip.query.all()
    task_trip_pairs = _get_new_trips_pairs()
    for trip in legacy_trips:
        if trip.pickup_location:
            counter[trip.pickup_location] += 1
    for task, trip in task_trip_pairs:
        req = task.request if task else None
        if req and req.pickup_location:
            counter[req.pickup_location] += 1
    return jsonify([
        {
            "location": location,
            "count": count
        }
        for location, count in counter.most_common(8)
    ])

@analytics_bp.route('/api/analytics/route-frequency', methods=['GET'])

@login_required

def analytics_route_frequency():

    legacy_trips = AmbulanceTrip.query.all()

    new_trips = Trip.query.all()

    segment_counter = Counter()

    segment_coords = {}

    all_geometries = []

    # Collect legacy routes

    for trip in legacy_trips:

        geom = _safe_parse_geometry(trip.route_geometry)

        if geom and len(geom) > 1:

            all_geometries.append(geom)

    # Collect new routes

    for trip in new_trips:

        geom = _safe_parse_geometry(trip.route_geometry)

        if geom and len(geom) > 1:

            all_geometries.append(geom)

    # Build segment frequency

    for geom in all_geometries:

        step = 1

        if len(geom) > 80:

            step = 2

        if len(geom) > 200:

            step = 4

        for i in range(0, len(geom) - 1, step):

            p1 = geom[i]

            p2 = geom[i + 1]

            if not isinstance(p1, list) or not isinstance(p2, list):

                continue

            if len(p1) < 2 or len(p2) < 2:

                continue

            key = _segment_key(p1, p2)

            segment_counter[key] += 1

            if key not in segment_coords:

                segment_coords[key] = [p1, p2]

    if not segment_counter:

        return jsonify([])

    max_count = max(segment_counter.values())

    results = []

    for key, count in segment_counter.most_common(50):

        normalized = round(count / max_count, 3)

        if normalized >= 0.7:

            risk = "High"

            color = "red"

        elif normalized >= 0.4:

            risk = "Medium"

            color = "orange"

        else:

            risk = "Low"

            color = "green"

        results.append({

            "frequency": count,

            "normalized_frequency": normalized,

            "risk": risk,

            "color": color,

            "coordinates": segment_coords[key]

        })

    return jsonify(results)

@analytics_bp.route('/api/analytics/emergency-zones', methods=['GET'])
@login_required
def analytics_emergency_zones():
    zone_counter = Counter()
    location_meta = {}
    legacy_trips = AmbulanceTrip.query.all()
    task_trip_pairs = _get_new_trips_pairs()

    for trip in legacy_trips:
        if trip.pickup_location:
            zone_counter[trip.pickup_location] += 1
            location_meta[trip.pickup_location] = {
                'lat': trip.pickup_lat,
                'lon': trip.pickup_lon
            }
            
    for task, trip in task_trip_pairs:
        req = task.request if task else None
        if req and req.pickup_location:
            zone_counter[req.pickup_location] += 1
            location_meta[req.pickup_location] = {
                'lat': req.latitude,
                'lon': req.longitude
            }
           
    if not zone_counter:
        return jsonify([])
    
    max_count = max(zone_counter.values())
    results = []
    
    for location, count in zone_counter.most_common():
        meta = location_meta.get(location, {})
        lat = meta.get("lat")
        lon = meta.get('lon')

        if lat is None or lon is None:
            continue
        normalized = round(count/max_count,3)
        if normalized >=0.7:
            risk = "High Demand"
            color = "red"
            radius = 170
        elif normalized >= 0.4:
            risk = "Medium Demand"
            color = "orange"
            radius = 125
        else:
            risk = "Low Demand"
            color = "green"
            radius = 85
        results.append({
            "location": location,
            "count": count,
            "risk": risk,
            "color": color,
            "radius": radius,
            "lat": lat,
            "lon": lon
        })
    return jsonify(results)
