"""
GeoMed Trips & Legacy API
Preserves original submission API for backward compatibility.
"""
from flask import jsonify, request, current_app
from extensions import db
from models import AmbulanceTrip, Trip
from datetime import datetime
import json
from . import api_bp


@api_bp.route('/trips/submit', methods=['POST'])
def submit_trip():
    """Legacy backward-compatible trip submission endpoint."""
    try:
        data = request.get_json(silent=True) or {}
        trip = AmbulanceTrip(
            date=data['date'],
            time=data['time'],
            km_reading_start=float(data['km_reading_start']),
            km_reading_end=float(data['km_reading_end']),
            pickup_location=data['pickup_location'],
            pickup_lat=float(data['pickup_lat']),
            pickup_lon=float(data['pickup_lon']),
            patient_name=data['patient_name'],
            driver_name=data['driver_name'],
            purpose=data['purpose'],
            notes=data.get('notes', ''),
            distance_km=float(data['distance_km']),
            duration_minutes=float(data['duration_minutes']),
            departure_time=data['departure_time'],
            arrival_time=data['arrival_time'],
            route_geometry=json.dumps(data.get('route_geometry', []))
        )
        db.session.add(trip)
        db.session.commit()
        return jsonify({"status": "success", "message": "Trip recorded successfully"})
    except Exception as e:
        current_app.logger.error(f"Error submitting trip: {str(e)}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

def _serialize_new_trip(trip):
    task = trip.task
    req = task.request if task and task.request else None
    patient = req.patient if req and req.patient else None
    ambulance = task.ambulance if task and task.ambulance else None

    created_dt = trip.created_at or datetime.utcnow()
    return {
        "id": f'new-{trip.id}',
        "date": created_dt.strftime('%Y-%m-%d'),
        "time": created_dt.strftime('%H:%M'),
        "km_reading_start": trip.start_odometer or 0,
        "km_reading_end": trip.end_odometer or 0,
        "pickup_location": req.pickup_location if req else '',
        "pickup_lat": req.latitude if req else None,
        "pickup_lon": req.longitude if req else None,
        "patient_name": patient.name if patient else '',
        "driver_name": ambulance.driver_name if ambulance else '',
        "purpose": trip.incident_category or (req.emergency_type if req else 'Trip'),
        "notes": task.driver_notes if task else '',
        "distance_km": trip.distance_km or 0,
        "duration_minutes": trip.duration_minutes or 0,
        "estimated_duration_minutes": task.estimated_duration_min if task else None,
        "departure_time": task.assigned_time.strftime('%H:%M') if task and task.assigned_time else '',
        "arrival_time": task.completed_time.strftime('%H:%M') if task and task.completed_time else '',
        "route_geometry": trip.route_geometry if trip.route_geometry else json.dumps([]),
        "created_at": created_dt.isoformat(),
        "source_model" : 'Trip',
        "route_source": trip.route_source or 'Simulated',
        "campus_zone": trip.campus_zone,
        "hostel": trip.hostel,
        "response_time_minutes": trip.response_time_minutes or 0,
    }

@api_bp.route('/trips', methods=['GET'])
def get_trips():
    """Get all trips for visualization."""
    legacy_trips = [trip.to_dict() for trip in AmbulanceTrip.query.all()]
    new_trips = [_serialize_new_trip(trip) for trip in Trip.query.all()]
    combined = legacy_trips + new_trips
    def sort_key(item):
        return item.get('created_at') or ''
    
    combined.sort(key=sort_key, reverse=True)
    return jsonify(combined)