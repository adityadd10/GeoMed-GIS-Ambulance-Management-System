from flask import Blueprint

driver_bp = Blueprint('driver', __name__, template_folder='../../templates')

from . import routes  # noqa: F401, E402
