from flask import Blueprint

schedules_bp = Blueprint('schedules', __name__)

from app.schedules import routes  # noqa: E402, F401
