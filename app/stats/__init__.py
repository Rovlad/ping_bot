from flask import Blueprint

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')

from app.stats import routes  # noqa: E402, F401
