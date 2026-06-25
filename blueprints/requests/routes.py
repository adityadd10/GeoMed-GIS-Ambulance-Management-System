"""
GeoMed Patient Requests Blueprint
"""
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from models import Patient, PatientRequest
from datetime import datetime
from . import requests_bp


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
    locations = cfg.Config.CAMPUS_LOCATIONS
    emergency_types = PatientRequest.EMERGENCY_TYPES
    if request.method == 'POST':
        try:
            data = request.form
            # Create or find patient
            patient_name = (data.get('patient_name') or '').strip()
            if not patient_name:
                flash('Patient name is required.', 'danger')
                return render_template('requests_new.html', page='requests',
                                       locations=locations, emergency_types=emergency_types)
            try:
                lat = float(data.get('latitude', 19.1309507))
                lon = float(data.get('longitude', 72.9146062))
            except ValueError:
                flash('Invalid latitude or longitude.', 'danger')
                return render_template('requests_new.html', page='requests',
                                       locations=locations, emergency_types=emergency_types)
            
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
                symptoms=data.get('symptoms'),
                emergency_type=data.get('emergency_type', 'unknown'),
                pickup_location=data.get('pickup_location'),
                latitude=lat,
                longitude=lon,
                notes=data.get('notes'),
                status=PatientRequest.STATUS_PENDING,
            )

            # Try ML classification
            try:
                from ml.classifier import classify_emergency
                symptoms_text = data.get('symptoms', '')
                if symptoms_text:
                    result = classify_emergency(symptoms_text)
                    patient_request.ml_emergency_type = result.get('emergency_type')
                    patient_request.ml_confidence = result.get('confidence')
                    if patient_request.emergency_type == 'unknown':
                        patient_request.emergency_type = result.get('emergency_type', 'unknown')
            except Exception:
                pass  # ML graceful failure

            db.session.add(patient_request)
            db.session.commit()

            flash(f'Request #{patient_request.id} created successfully.', 'success')
            return redirect(url_for('requests.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating request: {str(e)}', 'danger')

    return render_template('requests_new.html', page='requests',
                           locations=locations, emergency_types=emergency_types)


@requests_bp.route('/requests/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_request(request_id):
    req = PatientRequest.query.get_or_404(request_id)
    req.status = PatientRequest.STATUS_CANCELLED
    req.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'Request #{request_id} cancelled.', 'warning')
    return redirect(url_for('requests.index'))
