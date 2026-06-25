"""
GeoMed Task Management Blueprint
"""
from flask import render_template
from flask_login import login_required
from models import Task, PatientRequest, Ambulance
from . import tasks_bp


@tasks_bp.route('/tasks')
@login_required
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template('tasks.html', tasks=tasks, page='tasks')
