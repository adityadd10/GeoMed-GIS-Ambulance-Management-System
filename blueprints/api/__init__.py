from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import gis, dispatch, trips, ml_routes  # noqa: F401, E402
