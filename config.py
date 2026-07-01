"""
GeoMed Configuration
All secrets loaded from .env. See .env.example.
Database: PostgreSQL (primary), SQLite (local fallback).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'geomed-dev-secret-change-in-production')

    # Database — PostgreSQL primary, SQLite fallback
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL if DATABASE_URL else 'sqlite:///geomed.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # PostGIS optional spatial extension
    POSTGIS_ENABLED = os.environ.get('POSTGIS_ENABLED', 'false').lower() == 'true'

    # OpenRouteService
    ORS_API_KEY = os.environ.get('ORS_API_KEY', '')

    # Routing
    ROUTING_TIMEOUT = int(os.environ.get('ROUTING_TIMEOUT', '10'))
    HAVERSINE_SPEED_KMH = 30

    # IITB Hospital
    HOSPITAL_COORDS = [19.1309507, 72.9146062]
    HOSPITAL_NAME = 'IITB Hospital'

    # Initial odometer
    INITIAL_ODOMETER = 0

    # Flask
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    PORT = int(os.environ.get('PORT', '5001'))

    # Campus Locations
    CAMPUS_LOCATIONS = {
        'Hostel 1 (Queen of the Campus)': [19.1360511, 72.9139822],
        'Hostel 2 (The Wild Ones)': [19.1360302, 72.9125194],
        'Hostel 3 (Vitruvians)': [19.1360347, 72.9114388],
        'Hostel 4 (Madhouse)': [19.1360347, 72.9114388],
        'Hostel 5 (Penthouse)': [19.1353150, 72.9103374],
        'Hostel 6 (Vikings)': [19.1352447, 72.9070937],
        'Hostel 8': [19.1339352, 72.9112112],
        'Hostel 9 (Pluto)': [19.1349887, 72.9081793],
        'Hostel 10 (Phoenix)': [19.1296172, 72.9159134],
        'Hostel 11 (Athena)': [19.1335136, 72.9122780],
        'Hostel 12 (Crown of the Campus)': [19.1355082, 72.9057432],
        'Hostel 13 (House of Titans)': [19.1355082, 72.9057432],
        'Hostel 14 (The Silicon Ship)': [19.1355082, 72.9057432],
        'Hostel 15 (Trident)': [19.1374068, 72.9135782],
        'Hostel 16 (Olympus)': [19.1377654, 72.9128483],
        'Hostel 17 (Kings Landing)': [19.1348411, 72.9086540],
        'Hostel 18': [19.1360071, 72.9094808],
        'Tansa': [19.1357613, 72.9104464],
        'Main Gate': [19.1272, 72.9134],
        'Lecture Hall Complex (LHC)': [19.1329, 72.9147],
        'SAC (Student Activity Centre)': [19.1336, 72.9168],
        'Powai Lake': [19.1273, 72.9098],
    }


 # ------------------------------------------------------------------

    # Campus routing overrides

    # Display coordinates can be inside buildings, while routing

    # coordinates are snapped to nearby roads for better navigation.

    # ------------------------------------------------------------------

    CAMPUS_ROUTE_OVERRIDES = {

        # Example:

        # 'Hostel 1 (Queen of the Campus)': [19.135980, 72.914120],

        # 'Main Gate': [19.127200, 72.913400],

    }

    # Optional GeoJSON overlay

    CAMPUS_BUILDINGS_GEOJSON = '/static/data/iitb_buildings.geojson'
    CAMPUS_ROADS_GEOJSON = '/static/data/iitb_road_geojson.geojson'

    @classmethod
    def get_route_coords(cls, location_name):
        return cls.CAMPUS_LOCATIONS.get(location_name) 
    
    @classmethod
    def get_route_coords(cls, location_name):
        return cls.CAMPUS_ROUTE_OVERRIDES.get(location_name) or cls.CAMPUS_LOCATIONS.get(location_name)   

    @classmethod
    def get_campus_locations_from_geojson(cls):
        import os
        import json

        path = os.path.join(os.getcwd(), 'static', 'data', 'iitb_buildings.geojson')
        if not os.path.exists(path):
            return cls.CAMPUS_LOCATIONS
        try:
            with open(path, 'r', encoding = 'utf-8') as f:
                data = json.load(f)
            locations = {}
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                name = props.get('Name')
                lat = props.get("latitude")
                lon = props.get("longitude")
                if name and lat is not None and lon is not None:
                    locations[name] = [float(lat),float(lon)]
            return locations if locations else cls.CAMPUS_LOCATIONS
        except Exception as e:
            print(f"Error reading campus geojson: {e}")
            return cls.CAMPUS_LOCATIONS     
            

class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
