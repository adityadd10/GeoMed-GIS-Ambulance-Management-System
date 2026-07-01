"""
GeoMed Patient Requests Blueprint
"""
from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Patient, PatientRequest
from datetime import datetime
from . import requests_bp
import os
import json


def load_incident_catalog():
    path = os.path.join(current_app.root_path, 'static', 'data', 'incidents.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get('incidents', [])
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        current_app.logger.error(f"Error loading incident catalog: {e}")
        return []
    
def find_incident_by_id(incidents, incident_id):
    if not incident_id:
        return None
    try:
        incident_id = int(incident_id)
    except Exception:
        return None
    for incident in incidents:
        try:
            if int(incident.get('id')) == incident_id:
                return incident
        except Exception:
            continue
    return None

def find_incident_by_name(incidents, incident_name):
    if not incident_name:
        return None
    incident_name_normalized = incident_name.strip().lower()
    for incident in incidents:
        if incident.get('incident_name', '').strip().lower() == incident_name_normalized:
            return incident
    return None

def emergency_type_from_criticality(criticality_name):
    if not criticality_name:
        return 'unknown'
    value = criticality_name.strip().lower()

    if value == 'critical':
        return 'critical'
    if value in ['high', 'severe', 'urgent']:
        return 'urgent'
    if value in ['medium', 'moderate','low','minor']:
        return 'routine'
    return 'unknown'




@requests_bp.route('/requests')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    if status_filter != 'all':
        reqs = PatientRequest.query.filter_by(status=status_filter).order_by(
            PatientRequest.created_at.desc()).all()
    else:
        reqs = PatientRequest.query.order_by(PatientRequest.created_at.desc()).all()

    status_counts = {
        'pending': PatientRequest.query.filter_by(status='pending').count(),
        'assigned': PatientRequest.query.filter_by(status='assigned').count(),
        'in_progress': PatientRequest.query.filter_by(status='in_progress').count(),
        'completed': PatientRequest.query.filter_by(status='completed').count(),
        'cancelled': PatientRequest.query.filter_by(status='cancelled').count(),
    }
    return render_template('requests.html', requests=reqs,
                           status_counts=status_counts, page='requests',
                           current_filter=status_filter)


@requests_bp.route('/requests/new', methods=['GET', 'POST'])
@login_required
def new_request():
    import config as cfg
    locations = cfg.Config.get_campus_locations_from_geojson()
    incidents = load_incident_catalog()
    if request.method == 'POST':
        try:
            data = request.form
            # Create or find patient
            patient_name = (data.get('patient_name') or '').strip()
            if not patient_name:
                flash('Patient name is required.', 'danger')
                return render_template('requests_new.html', page='requests',
                                       locations=locations, incidents=incidents)
            incident_input = data.get('incident_name') or ''.strip()
            incident_id = data.get('incident_id') 
            selected_incident = find_incident_by_id(incidents, incident_id) 
            if not selected_incident:
                selected_incident = find_incident_by_name(incidents, incident_input)
            if selected_incident:
                incident_category = selected_incident.get('category')
                incident_name = selected_incident.get('incident_name')
                criticality_level = selected_incident.get('criticality_level')
                criticality_name = selected_incident.get('criticality_name')
                emergency_type = emergency_type_from_criticality(criticality_name)
            else:
                incident_category = 'Other'
                incident_name = incident_input if incident_input else 'Unknown'
                criticality_level = None
                criticality_name = 'Unknown' 
                emergency_type = 'unknown'

            try:
                lat = float(data.get('latitude', 19.1309507))
                lon = float(data.get('longitude', 72.9146062))
            except ValueError:
                flash('Invalid latitude or longitude.', 'danger')
                return render_template('requests_new.html', page='requests',
                                       locations=locations, incidents=incidents)
            
            patient = Patient(
                name=patient_name,
                age = data.get('patient_age', type=int) or None,
                gender=data.get('patient_gender'),
                phone=data.get('patient_phone'),
                hostel=data.get('patient_hostel'),
                roll_number=data.get('roll_number'),
            )
            db.session.add(patient)
            db.session.flush()  # get patient.id

            lat = float(data.get('latitude', 19.1309507))
            lon = float(data.get('longitude', 72.9146062))

            patient_request = PatientRequest(
                patient_id=patient.id,
                created_by_id=current_user.id,
                symptoms=None,
                incident_category=incident_category,
                incident_name=incident_name,
                criticality_level=criticality_level,
                criticality_name=criticality_name,
                emergency_type=emergency_type,
                pickup_location=data.get('pickup_location'),
                latitude=lat,
                longitude=lon,
                notes=data.get('notes'),
                status=PatientRequest.STATUS_PENDING,
            )

            db.session.add(patient_request)
            db.session.commit()

            flash(f'Request #{patient_request.id} created successfully.', 'success')
            return redirect(url_for('requests.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating request: {str(e)}', 'danger')

    return render_template('requests_new.html', page='requests',
                           locations=locations, incidents=incidents)


@requests_bp.route('/requests/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_request(request_id):
    req = PatientRequest.query.get_or_404(request_id)
    req.status = PatientRequest.STATUS_CANCELLED
    req.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'Request #{request_id} cancelled.', 'warning')
    return redirect(url_for('requests.index'))
