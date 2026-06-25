"""
GeoMed Admin Blueprint
"""
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db, bcrypt
from models import User, Ambulance
from blueprints.auth.routes import role_required
from . import admin_bp


@admin_bp.route('/admin')
@login_required
@role_required('admin')
def index():
    users = User.query.order_by(User.created_at.desc()).all()
    ambulances = Ambulance.query.order_by(Ambulance.created_at.desc()).all()
    return render_template('admin.html', users=users, ambulances=ambulances, page='admin')


@admin_bp.route('/admin/users/new', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    try:
        user = User(
            name=request.form.get('name'),
            username=request.form.get('username'),
            role=request.form.get('role', 'staff'),
        )
        user.set_password(request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} created.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.index'))


@admin_bp.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} {status}.', 'info')
    return redirect(url_for('admin.index'))


@admin_bp.route('/admin/ambulances/new', methods=['POST'])
@login_required
@role_required('admin')
def create_ambulance():
    try:
        ambulance = Ambulance(
            vehicle_number=request.form.get('vehicle_number'),
            driver_name=request.form.get('driver_name'),
            status=request.form.get('status', 'available'),
            current_odometer=float(request.form.get('current_odometer', 0)),
        )
        driver_user_id = request.form.get('driver_user_id')
        if driver_user_id:
            ambulance.driver_user_id = int(driver_user_id)
        db.session.add(ambulance)
        db.session.commit()
        flash(f'Ambulance {ambulance.vehicle_number} added.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.index'))


@admin_bp.route('/admin/ambulances/<int:amb_id>/status', methods=['POST'])
@login_required
@role_required('admin')
def update_ambulance_status(amb_id):
    ambulance = Ambulance.query.get_or_404(amb_id)
    ambulance.status = request.form.get('status', ambulance.status)
    db.session.commit()
    flash(f'Ambulance {ambulance.vehicle_number} status updated.', 'info')
    return redirect(url_for('admin.index'))
