"""
GeoMed Dispatch API
"""
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Task, PatientRequest, Ambulance
from . import api_bp
from route_optimizer import calculate_route



@api_bp.route('/dispatch/assign', methods=['POST'])
@login_required 
def assign_task():
    data = request.get_json(silent=True) or {}
    request_id = data.get('request_id')
    ambulance_id = data.get('ambulance_id')
    if not request_id or not ambulance_id:
        return jsonify({'error': 'Missing request_id or ambulance _id'}), 400
    
    req = PatientRequest.query.get(request_id)
    amb = Ambulance.query.get(ambulance_id)

    if not req or not amb:
        return jsonify({'error': 'Request or Ambulance not found'}), 404

    # Prevent invalid reassignment
    if req.status!= PatientRequest. STATUS_PENDING:
        return jsonify({'error': f'Request #{req.id} is already in a different status'}), 400
    if req. task is not None:
        return jsonify({'error': f'Request #{req.id} already has a task assigned'}), 400
    if amb. status != Ambulance. STATUS_AVAILABLE:
        return jsonify({'error': f'Ambulance #{amb.vehicle_number} is currently {amb.status}'}), 400

    # Calculate estimated distance/time
    try:
        route_data = calculate_route(
            [amb.current_lon, amb.current_lat],
            [req.longitude, req.latitude],
            current_app.config.get('ORS_API_KEY')
        )
        est_dist = route_data.get('distance', 0)

        raw_duration = route_data.get('duration', 0)
        est_dur = max((raw_duration * 1.35) + 2,5)

    except Exception as e:
        current_app.logger.warning(f"Route calculation failed during dispatch: {str (e)}")
        est_dist = 0
        est_dur = 6

    task = Task(
        request_id=req.id,
        ambulance_id=amb.id,
        assigned_by_id=current_user.id,
        status=Task.STATUS_ASSIGNED,
        estimated_distance_km=est_dist,
        estimated_duration_min=est_dur
    )

    req.status = PatientRequest.STATUS_ASSIGNED
    amb.status = Ambulance.STATUS_BUSY
    db.session.add(task)
    db.session.commit()
    return jsonify({'message': 'Task assigned successfully', 'task_id': task.id})

