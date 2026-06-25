from flask import Blueprint

requests_bp = Blueprint('requests', __name__, template_folder='../../templates')

from . import routes  # noqa: F401, E402
