"""
GeoMed Driver Portal Blueprint
"""
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Task, Trip, Ambulance, PatientRequest
from . import driver_bp
from datetime import datetime


def _get_driver_ambulance():
    return Ambulance.query.filter_by(driver_user_id=current_user.id).first()

def _task_belongs_to_current_driver(task):
    ambulance = _get_driver_ambulance()
    return ambulance is not None and task.ambulance_id == ambulance.id

def _update_task_status(task, new_status, success_message):
    if not _task_belongs_to_current_driver(task):
        flash('You are not authorized to update this task.', 'danger')
        return False
    task.status = new_status
    db.session.commit()
    flash(success_message, 'success')
    return True

@driver_bp.route('/driver')
@login_required
def index():
    ambulance = _get_driver_ambulance()
    active_task = None
    if ambulance:
        active_task = Task.query.filter(
            Task.ambulance_id == ambulance.id,
            Task.status.in_([
                Task.STATUS_ASSIGNED,
                Task.STATUS_ACCEPTED,
                Task.STATUS_EN_ROUTE,
                Task.STATUS_AT_SCENE,
                Task.STATUS_TRANSPORTING
            ])
        ).order_by(Task.created_at.desc()).first()
    return render_template('driver.html', page='driver',
                           ambulance=ambulance, active_task=active_task)


@driver_bp.route('/driver/task/<int:task_id>/accept', methods=['POST'])
@login_required
def accept_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not _task_belongs_to_current_driver(task):
        flash('You are not authorized to accept this task.', 'danger')
        return redirect(url_for('driver.index'))
    if task.status != Task. STATUS_ASSIGNED:
        flash(f'Task #{task.id} cannot be accepted because it is {task. status}.', 'warning')
        return redirect(url_for('driver.index'))
    task. status = Task.STATUS_ACCEPTED 
    task.accepted_time = datetime.utcnow()
    
    if task.request:
        task.request.status = PatientRequest.STATUS_IN_PROGRESS

    db.session.commit()
    flash('Task accepted. En route to patient.', 'success')
    return redirect(url_for('driver.index'))

@driver_bp.route('/driver/task/<int:task_id>/en-route', methods=['POST'])
@login_required
def en_route_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.status not in [Task.STATUS_ACCEPTED]:
        flash(f'Task #{task.id} must be accepted before marking en route.', 'warning')
        return redirect(url_for('driver.index'))
    _update_task_status(task, Task.STATUS_EN_ROUTE, 'Status updated: En route to patient.')
    return redirect(url_for('driver.index'))

@driver_bp.route('/driver/task/<int:task_id>/at-scene', methods=['POST'])
@login_required
def mark_at_scene(task_id):
    task = Task.query.get_or_404(task_id)
    if task.status not in [Task.STATUS_EN_ROUTE]:
        flash(f'Task #{task.id} must be en route before marking at scene.', 'warning')
        return redirect(url_for('driver.index'))
    _update_task_status(task, Task.STATUS_AT_SCENE, 'Status updated: At scene.')
    return redirect(url_for('driver.index'))

@driver_bp.route('/driver/task/<int:task_id>/transporting', methods=['POST'])
@login_required
def mark_transporting(task_id):
    task = Task.query.get_or_404(task_id)
    if task.status not in [Task.STATUS_AT_SCENE]:
        flash(f'Task #{task.id} must be at scene before marking transporting.', 'warning')
        return redirect(url_for('driver.index'))
    _update_task_status(task, Task.STATUS_TRANSPORTING, 'Status updated: Transporting patient.')
    return redirect(url_for('driver.index'))

@driver_bp.route('/driver/task/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not _task_belongs_to_current_driver(task):
        flash('You are not authorized to complete this task.', 'danger')
        return redirect(url_for('driver.index'))
    if task.status not in [
        Task.STATUS_ASSIGNED,
        Task.STATUS_ACCEPTED,
        Task.STATUS_EN_ROUTE,
        Task.STATUS_AT_SCENE,
        Task.STATUS_TRANSPORTING
    ]:
        flash(f'Task #{task.id} cannot be completed because it is {task.status}.', 'warning')
        return redirect(url_for('driver.index'))
    
    try:
        start_odo = float(request. form.get('start_odometer', 0) or 0)
        end_odo = float(request.form.get('end_odometer', 0) or 0)
    except ValueError:
        flash(' Invalid odometer values.', 'danger')
        return redirect(url_for('driver.index'))

    notes = request.form.get('driver_notes', '')
    route_geometry = request.form.get('route_geometry', '')
    route_source = request.form.get('route_source', 'Simulated')

    task.status = Task.STATUS_COMPLETED
    task.completed_time = datetime.utcnow()
    task.driver_notes = notes

    if task.request:
        task.request.status = PatientRequest.STATUS_COMPLETED
    ambulance = task.ambulance
    if ambulance:
        ambulance.status = Ambulance.STATUS_AVAILABLE
        if end_odo > 0:
            ambulance.current_odometer = end_odo
    if end_odo > 0 and start_odo > 0 and end_odo >= start_odo:
        distance = end_odo - start_odo
    else:   
        distance = task.estimated_distance_km or 0

    response_time_minutes = None
    if task.assigned_time and task.accepted_time:
        response_time_minutes = round((task.accepted_time - task.assigned_time).total_seconds() / 60, 2)
    actual_duration_minutes = None
    if task.accepted_time and task.completed_time:
        actual_duration_minutes = round((task.completed_time - task.accepted_time).total_seconds() / 60, 2)

    req = task.request
    patient = req.patient if req and req.patient else None        

    trip = Trip(
        task_id=task.id,
        distance_km=distance,
        duration_minutes=actual_duration_minutes if actual_duration_minutes is not None else task.estimated_duration_min,
        start_odometer=start_odo,
        end_odometer=end_odo,
        route_geometry=route_geometry if route_geometry else None,
        route_source=route_source,
        incident_category = (
            req.incident_category if req and req.incident_category else 
            req.emergency_type if req and req else None
        ),
        campus_zone = None,
        hostel = patient.hostel if patient else None,
        weather_condition = None,
        temperature = None,
        response_time_minutes=response_time_minutes
    )
    db.session.add(trip)
    db.session.commit()
    flash('Trip completed successfully.', 'success')
    return redirect(url_for('driver.index'))

