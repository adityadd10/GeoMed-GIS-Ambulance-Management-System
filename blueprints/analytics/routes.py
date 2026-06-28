"""
GeoMed Analytics API

Phase 5: Advanced analytics + route frequency intelligence

"""


from collections import Counter

from datetime import datetime, date

from flask import jsonify

from flask_login import login_required

from extensions import db

from models import Trip, Task, AmbulanceTrip

from . import analytics_bp

import json

from flask import render_template



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



def _get_all_legacy_trips():

    return AmbulanceTrip.query.all()



def _get_all_new_trips():

    return Trip.query.all()



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



@analytics_bp.route('/analytics')

@login_required

def index():

    return render_template('analytics.html', page='analytics')


@analytics_bp.route('/api/analytics/overview', methods=['GET'])

@login_required

def analytics_overview():

    legacy_trips = _get_all_legacy_trips()

    new_trips = _get_all_new_trips()

    total_trips = len(legacy_trips) + len(new_trips)

    total_distance = (

        sum(t.distance_km or 0 for t in legacy_trips) +

        sum(t.distance_km or 0 for t in new_trips)

    )

    completed_task_trip_pairs = (

        db.session.query(Task, Trip)

        .join(Trip, Trip.task_id == Task.id)

        .all()

    )

    eta_values = [

        task.estimated_duration_min

        for task, trip in completed_task_trip_pairs

        if task.estimated_duration_min is not None

    ]

    actual_values = [

        trip.duration_minutes

        for trip in new_trips

        if trip.duration_minutes is not None

    ] + [

        trip.duration_minutes

        for trip in legacy_trips

        if trip.duration_minutes is not None

    ]

    response_values = [

        trip.response_time_minutes

        for trip in new_trips

        if trip.response_time_minutes is not None

    ]

    hour_counter = Counter()

    for trip in legacy_trips:

        dt = _parse_legacy_datetime(trip.date, trip.time)

        if dt:

            hour_counter[dt.hour] += 1

    for trip in new_trips:

        if trip.created_at:

            hour_counter[trip.created_at.hour] += 1

    peak_hour = None

    peak_count = 0

    if hour_counter:

        peak_hour, peak_count = hour_counter.most_common(1)[0]

    return jsonify({

        "total_trips": total_trips,

        "total_distance_km": round(total_distance, 2),

        "avg_eta_min": _safe_avg(eta_values),

        "avg_actual_time_min": _safe_avg(actual_values),

        "avg_response_time_min": _safe_avg(response_values),

        "peak_hour": peak_hour,

        "peak_hour_count": peak_count

    })

@analytics_bp.route('/api/analytics/highlights', methods=['GET'])

@login_required

def analytics_highlights():

    legacy_trips = _get_all_legacy_trips()

    new_trips = _get_all_new_trips()

    today = date.today()

    completed_today = 0

    for trip in legacy_trips:

        dt = _parse_legacy_datetime(trip.date, trip.time)

        if dt and dt.date() == today:

            completed_today += 1

    for trip in new_trips:

        if trip.created_at and trip.created_at.date() == today:

            completed_today += 1

    category_counter = Counter()

    hostel_counter = Counter()

    ambulance_counter = Counter()

    for trip in legacy_trips:

        category_counter[trip.purpose or "Unknown"] += 1

    task_trip_pairs = (

        db.session.query(Task, Trip)

        .join(Trip, Trip.task_id == Task.id)

        .all()

    )

    for task, trip in task_trip_pairs:

        category_counter[trip.incident_category or task.request.emergency_type if task.request else "Unknown"] += 1

        hostel_counter[trip.hostel or "Unknown"] += 1

        if task.ambulance:

            ambulance_counter[task.ambulance.vehicle_number] += 1

    top_category = category_counter.most_common(1)[0] if category_counter else ("Unknown", 0)

    top_hostel = hostel_counter.most_common(1)[0] if hostel_counter else ("Unknown", 0)

    busiest_ambulance = ambulance_counter.most_common(1)[0] if ambulance_counter else ("Unknown", 0)

    return jsonify({

        "completed_today": completed_today,

        "top_category": {"name": top_category[0], "count": top_category[1]},

        "top_hostel": {"name": top_hostel[0], "count": top_hostel[1]},

        "busiest_ambulance": {"name": busiest_ambulance[0], "count": busiest_ambulance[1]}

    })


@analytics_bp.route('/api/analytics/trips-by-day', methods=['GET'])

@login_required

def analytics_trips_by_day():

    legacy_trips = _get_all_legacy_trips()

    new_trips = _get_all_new_trips()

    counter = Counter()

    for trip in legacy_trips:

        dt = _parse_legacy_datetime(trip.date, trip.time)

        if dt:

            counter[dt.strftime("%Y-%m-%d")] += 1

    for trip in new_trips:

        if trip.created_at:

            counter[trip.created_at.strftime("%Y-%m-%d")] += 1

    results = [{"date": day, "count": counter[day]} for day in sorted(counter.keys())]

    return jsonify(results)


@analytics_bp.route('/api/analytics/trips-by-hour', methods=['GET'])

@login_required

def analytics_trips_by_hour():

    legacy_trips = _get_all_legacy_trips()

    new_trips = _get_all_new_trips()

    counter = Counter({h: 0 for h in range(24)})

    for trip in legacy_trips:

        dt = _parse_legacy_datetime(trip.date, trip.time)

        if dt:

            counter[dt.hour] += 1

    for trip in new_trips:

        if trip.created_at:

            counter[trip.created_at.hour] += 1

    results = [{"hour": hour, "count": counter[hour]} for hour in range(24)]

    return jsonify(results)


@analytics_bp.route('/api/analytics/category-distribution', methods=['GET'])

@login_required

def analytics_category_distribution():

    legacy_trips = _get_all_legacy_trips()

    new_trips = _get_all_new_trips()

    counter = Counter()

    for trip in legacy_trips:

        category = trip.purpose or "Unknown"

        counter[category] += 1

    for trip in new_trips:

        category = trip.incident_category or "Unknown"

        counter[category] += 1

    results = [{"category": key, "count": value} for key, value in counter.most_common()]

    return jsonify(results)


@analytics_bp.route('/api/analytics/hostel-distribution', methods=['GET'])

@login_required

def analytics_hostel_distribution():

    new_trips = _get_all_new_trips()

    counter = Counter()

    for trip in new_trips:

        hostel = trip.hostel or "Unknown"

        counter[hostel] += 1

    results = [{"hostel": key, "count": value} for key, value in counter.most_common()]

    return jsonify(results)


@analytics_bp.route('/api/analytics/zone-distribution', methods=['GET'])

@login_required

def analytics_zone_distribution():

    new_trips = _get_all_new_trips()

    counter = Counter()

    for trip in new_trips:

        zone = trip.campus_zone or "Unknown"

        counter[zone] += 1

    results = [{"zone": key, "count": value} for key, value in counter.most_common()]

    return jsonify(results)


@analytics_bp.route('/api/analytics/busiest-ambulances', methods=['GET'])

@login_required

def analytics_busiest_ambulances():

    task_trip_pairs = (

        db.session.query(Task, Trip)

        .join(Trip, Trip.task_id == Task.id)

        .all()

    )

    counter = Counter()

    for task, trip in task_trip_pairs:

        if task.ambulance:

            counter[task.ambulance.vehicle_number] += 1

    results = [{"ambulance": key, "count": value} for key, value in counter.most_common()]

    return jsonify(results)


@analytics_bp.route('/api/analytics/performance', methods=['GET'])

@login_required

def analytics_performance():

    task_trip_pairs = (

        db.session.query(Task, Trip)

        .join(Trip, Trip.task_id == Task.id)

        .all()

    )

    eta_values = []

    actual_values = []

    response_values = []

    eta_gap_values = []

    on_time_count = 0

    for task, trip in task_trip_pairs:

        eta = task.estimated_duration_min

        actual = trip.duration_minutes

        response = trip.response_time_minutes

        if eta is not None:

            eta_values.append(eta)

        if actual is not None:

            actual_values.append(actual)

        if response is not None:

            response_values.append(response)

        if eta is not None and actual is not None:

            gap = actual - eta

            eta_gap_values.append(gap)

            if actual <= eta:

                on_time_count += 1

    completed_count = len(task_trip_pairs)

    on_time_rate = round((on_time_count / completed_count) * 100, 2) if completed_count else 0

    return jsonify({

        "completed_trip_count": completed_count,

        "avg_eta_min": _safe_avg(eta_values),

        "avg_actual_time_min": _safe_avg(actual_values),

        "avg_response_time_min": _safe_avg(response_values),

        "avg_eta_gap_min": _safe_avg(eta_gap_values),

        "on_time_rate_percent": on_time_rate

    })


@analytics_bp.route('/api/analytics/route-frequency', methods=['GET'])

@login_required

def analytics_route_frequency():

    """

    Builds a simple route frequency map from all trip geometries.

    Returns the most common repeated segments.

    """

    legacy_trips = _get_all_legacy_trips()

    new_trips = _get_all_new_trips()

    segment_counter = Counter()

    segment_coords = {}

    all_geometries = []

    for trip in legacy_trips:

        geom = _safe_parse_geometry(trip.route_geometry)

        if geom and len(geom) > 1:

            all_geometries.append(geom)

    for trip in new_trips:

        geom = _safe_parse_geometry(trip.route_geometry)

        if geom and len(geom) > 1:

            all_geometries.append(geom)

    for geom in all_geometries:

        # Sample every segment; if route is huge, lightly downsample

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

            key = _segment_key(p1, p2, precision=4)

            segment_counter[key] += 1

            if key not in segment_coords:

                segment_coords[key] = [p1, p2]

    if not segment_counter:

        return jsonify([])

    max_count = max(segment_counter.values())

    results = []

    for key, count in segment_counter.most_common(40):

        results.append({

            "coordinates": segment_coords[key],

            "frequency": count,

            "normalized_frequency": round(count / max_count, 3)

        })

    return jsonify(results)