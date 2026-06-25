"""
GeoMed ML API Routes
"""
from flask import jsonify, request
from flask_login import login_required
from . import api_bp

try:
    from ml.classifier import classify_emergency
    from ml.forecaster import forecast_demand
    from ml.hotspot import detect_hotspots
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


@api_bp.route('/ml/classify', methods=['POST'])
@login_required
def api_classify_emergency():
    if not ML_AVAILABLE:
        return jsonify({'error': 'ML modules not available (sklearn missing)'}), 503
    
    data = request.json
    symptoms = data.get('symptoms')
    if not symptoms:
        return jsonify({'error': 'Missing symptoms'}), 400
        
    result = classify_emergency(symptoms)
    return jsonify(result)


@api_bp.route('/ml/hotspots', methods=['GET'])
@login_required
def api_get_hotspots():
    if not ML_AVAILABLE:
        return jsonify({'error': 'ML modules not available (sklearn missing)'}), 503
        
    hotspots = detect_hotspots()
    return jsonify(hotspots)


@api_bp.route('/ml/forecast', methods=['GET'])
@login_required
def api_get_forecast():
    if not ML_AVAILABLE:
        return jsonify({'error': 'ML modules not available (sklearn missing)'}), 503
        
    days = int(request.args.get('days', 7))
    forecast = forecast_demand(days)
    return jsonify(forecast)
