from flask import Blueprint

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

from app.messages import routes  # noqa: E402, F401
