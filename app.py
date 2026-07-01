"""
GeoMed — Application Factory Entry Point
Replaces the legacy monolith.
"""
import os
from flask import Flask, render_template, jsonify
from extensions import db, login_manager, bcrypt, migrate
from config import config_map

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config_map[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    
    # Register user loader for Flask-Login
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Blueprints
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.requests import requests_bp
    from blueprints.tasks import tasks_bp
    from blueprints.driver import driver_bp
    from blueprints.analytics import analytics_bp
    from blueprints.admin import admin_bp
    from blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Legacy Fallback Route (preserves existing frontend)
    @app.route('/legacy')
    def legacy_index():
        return render_template('index.html')

    # Ensure tables exist (only for SQLite fallback)
    with app.app_context():
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            db.create_all()

    return app

# The instance used by Flask CLI and WSGI servers
app = create_app(os.environ.get('FLASK_ENV', 'default'))

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
