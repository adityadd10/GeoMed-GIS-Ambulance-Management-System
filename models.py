"""
GeoMed Database Models
Preserves original AmbulanceTrip model for backward compatibility.
Adds User, Ambulance, Patient, PatientRequest, Task, Trip models.
"""
from datetime import datetime
from flask_login import UserMixin
from extensions import db, bcrypt


# ─────────────────────────────────────────────
# PRESERVED — Backward Compatible
# ─────────────────────────────────────────────

class AmbulanceTrip(db.Model):
    """Legacy trip model — preserved for historical data compatibility."""
    __tablename__ = 'ambulance_trips'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    km_reading_start = db.Column(db.Float, nullable=False)
    km_reading_end = db.Column(db.Float, nullable=False)
    pickup_location = db.Column(db.String(100), nullable=False)
    pickup_lat = db.Column(db.Float, nullable=False)
    pickup_lon = db.Column(db.Float, nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    distance_km = db.Column(db.Float, nullable=False)
    duration_minutes = db.Column(db.Float, nullable=False)
    departure_time = db.Column(db.String(20), nullable=False)
    arrival_time = db.Column(db.String(20), nullable=False)
    route_geometry = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'time': self.time,
            'km_reading_start': self.km_reading_start,
            'km_reading_end': self.km_reading_end,
            'pickup_location': self.pickup_location,
            'pickup_lat': self.pickup_lat,
            'pickup_lon': self.pickup_lon,
            'patient_name': self.patient_name,
            'driver_name': self.driver_name,
            'purpose': self.purpose,
            'notes': self.notes,
            'distance_km': self.distance_km,
            'duration_minutes': self.duration_minutes,
            'departure_time': self.departure_time,
            'arrival_time': self.arrival_time,
            'route_geometry': self.route_geometry,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────
# NEW MODELS
# ─────────────────────────────────────────────

class User(UserMixin, db.Model):
    """System users: staff, driver, admin."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # staff | driver | admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assigned_ambulance = db.relationship('Ambulance', backref='driver_user', uselist=False,
                                          foreign_keys='Ambulance.driver_user_id')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Ambulance(db.Model):
    """Ambulance fleet management."""
    __tablename__ = 'ambulances'

    STATUS_AVAILABLE = 'available'
    STATUS_BUSY = 'busy'
    STATUS_MAINTENANCE = 'maintenance'
    STATUSES = [STATUS_AVAILABLE, STATUS_BUSY, STATUS_MAINTENANCE]

    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    driver_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='available')
    current_odometer = db.Column(db.Float, default=0.0)
    current_lat = db.Column(db.Float, default=19.1309507)
    current_lon = db.Column(db.Float, default=72.9146062)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = db.relationship('Task', backref='ambulance', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'driver_name': self.driver_name,
            'driver_user_id': self.driver_user_id,
            'status': self.status,
            'current_odometer': self.current_odometer,
            'current_lat': self.current_lat,
            'current_lon': self.current_lon,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Patient(db.Model):
    """Patient registry."""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    hostel = db.Column(db.String(100))
    building = db.Column(db.String(100))
    roll_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    requests = db.relationship('PatientRequest', backref='patient', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'phone': self.phone,
            'hostel': self.hostel,
            'building': self.building,
            'roll_number': self.roll_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PatientRequest(db.Model):
    """Patient ambulance requests."""
    __tablename__ = 'requests'

    STATUS_PENDING = 'pending'
    STATUS_ASSIGNED = 'assigned'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUSES = [STATUS_PENDING, STATUS_ASSIGNED, STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_CANCELLED]

    EMERGENCY_TYPES = ['critical', 'urgent', 'routine', 'transfer', 'unknown']

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    symptoms = db.Column(db.Text)
    incident_category = db.Column(db.String(100))
    incident_name = db.Column(db.String(100))
    criticality_level = db.Column(db.Integer)  
    criticality_name = db.Column(db.String(50))
    emergency_type = db.Column(db.String(50), default='unknown')
    pickup_location = db.Column(db.String(150))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    notes = db.Column(db.Text)
    request_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = db.relationship('Task', backref='request', uselist=False, lazy=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.name if self.patient else None,
            'symptoms': self.symptoms,
            'emergency_type': self.emergency_type,
            'incident_category': self.incident_category,
            'incident_name': self.incident_name,
            'criticality_level': self.criticality_level,
            'criticality_name': self.criticality_name,
            'pickup_location': self.pickup_location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'status': self.status,
            'notes': self.notes,
            'request_time': self.request_time.isoformat() if self.request_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Task(db.Model):
    """Dispatch tasks linking requests to ambulances."""
    __tablename__ = 'tasks'

    STATUS_ASSIGNED = 'assigned'
    STATUS_ACCEPTED = 'accepted'
    STATUS_EN_ROUTE = 'en_route'
    STATUS_AT_SCENE = 'at_scene'
    STATUS_TRANSPORTING = 'transporting'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False)
    ambulance_id = db.Column(db.Integer, db.ForeignKey('ambulances.id'), nullable=False)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='assigned')
    assigned_time = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_time = db.Column(db.DateTime)
    completed_time = db.Column(db.DateTime)
    driver_notes = db.Column(db.Text)
    estimated_distance_km = db.Column(db.Float)
    estimated_duration_min = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    trip = db.relationship('Trip', backref='task', uselist=False, lazy=True)
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id])

    @property
    def actual_duration_minutes(self):
        if self.assigned_time and self.completed_time:
            return round((self.completed_time - self.assigned_time).total_seconds() / 60, 2)
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'ambulance_id': self.ambulance_id,
            'ambulance_vehicle': self.ambulance.vehicle_number if self.ambulance else None,
            'status': self.status,
            'assigned_time': self.assigned_time.isoformat() if self.assigned_time else None,
            'accepted_time': self.accepted_time.isoformat() if self.accepted_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'driver_notes': self.driver_notes,
            'estimated_distance_km': self.estimated_distance_km,
            'estimated_duration_min': self.estimated_duration_min,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Trip(db.Model):
    """Completed trip data with GIS route geometry."""
    __tablename__ = 'trips'

    id = db.Column(db.Integer, primary_key=True)

    task_id = db.Column(
        db.Integer,
        db.ForeignKey('tasks.id'),
        nullable=False
    )

    # Trip Metrics
    distance_km = db.Column(db.Float)
    duration_minutes = db.Column(db.Float)

    start_odometer = db.Column(db.Float)
    end_odometer = db.Column(db.Float)

    # Route Data
    route_geometry = db.Column(db.Text)
    route_source = db.Column(db.String(30))

    # Analytics Fields
    incident_category = db.Column(db.String(100))
    campus_zone = db.Column(db.String(100))
    hostel = db.Column(db.String(100))

    weather_condition = db.Column(db.String(50))
    temperature = db.Column(db.Float)

    response_time_minutes = db.Column(db.Float)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,

            'distance_km': self.distance_km,
            'duration_minutes': self.duration_minutes,

            'start_odometer': self.start_odometer,
            'end_odometer': self.end_odometer,

            'route_geometry': self.route_geometry,
            'route_source': self.route_source,

            'incident_category': self.incident_category,
            'campus_zone': self.campus_zone,
            'hostel': self.hostel,

            'weather_condition': self.weather_condition,
            'temperature': self.temperature,

            'response_time_minutes': self.response_time_minutes,

            'created_at': self.created_at.isoformat()
            if self.created_at else None,
        }