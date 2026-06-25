"""

GeoMed GIS API

Improved for campus-aware routing and building overlay support.

"""

from flask import jsonify, request, current_app

from flask_login import login_required

from . import api_bp

from route_optimizer import calculate_route

from models import Ambulance, PatientRequest

import config

@api_bp.route('/gis/route', methods=['POST'])

@login_required

def get_route():

    data = request.get_json(silent=True) or {}

    # Coordinates are expected as [lat, lon]

    start = data.get('start')

    end = data.get('end')

    location_name = data.get('location_name')  # Optional campus location name

    if not start:

        return jsonify({'error': 'Missing start coordinates'}), 400

    # Resolve routing destination

    resolved_end = None

    if location_name:

        route_target = config.Config.get_route_coords(location_name)

        if route_target:

            resolved_end = route_target

    if not resolved_end:

        resolved_end = end

    if not resolved_end:

        return jsonify({'error': 'Missing destination coordinates'}), 400

    # calculate_route expects [lon, lat]

    route_data = calculate_route(

        [start[1], start[0]],

        [resolved_end[1], resolved_end[0]],

        current_app.config.get('ORS_API_KEY')

    )

    if route_data:

        return jsonify({

            **route_data,

            'display_destination': end,

            'routed_destination': resolved_end,

            'location_name': location_name

        })

    return jsonify({'error': 'Failed to calculate route'}), 500

@api_bp.route('/gis/ambulances', methods=['GET'])

@login_required

def get_ambulances():

    ambulances = Ambulance.query.all()

    return jsonify([amb.to_dict() for amb in ambulances])

@api_bp.route('/gis/requests/pending', methods=['GET'])

@login_required

def get_pending_requests():

    reqs = PatientRequest.query.filter_by(status='pending').all()

    return jsonify([r.to_dict() for r in reqs])

@api_bp.route('/gis/campus-locations', methods=['GET'])

@login_required

def get_campus_locations():

    """

    Returns all configured campus points with both display

    and routing coordinates.

    """

    points = []

    for name, display_coords in config.Config.CAMPUS_LOCATIONS.items():

        route_coords = config.Config.get_route_coords(name)

        points.append({

            'name': name,

            'display_lat': display_coords[0],

            'display_lon': display_coords[1],

            'route_lat': route_coords[0] if route_coords else display_coords[0],

            'route_lon': route_coords[1] if route_coords else display_coords[1],

            'has_override': name in config.Config.CAMPUS_ROUTE_OVERRIDES

        })

    return jsonify(points)

@api_bp.route('/gis/buildings-overlay', methods=['GET'])

@login_required

def get_buildings_overlay():

    """

    Returns the configured campus buildings GeoJSON path.

    """

    return jsonify({

        'geojson_url': config.Config.CAMPUS_BUILDINGS_GEOJSON

    })