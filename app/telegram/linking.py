import secrets
from datetime import datetime, timedelta

from app.extensions import db
from app.models import User


def generate_linking_code(user):
    """Generate a 6-char hex code, save to user, return it."""
    code = secrets.token_hex(3).upper()  # 6 hex chars
    user.linking_code = code
    user.linking_code_expires = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    return code


def validate_linking_code(code, telegram_chat_id, telegram_username):
    """Find user by code, link their Telegram, return True/False."""
    user = User.query.filter_by(linking_code=code.upper()).first()
    if not user or not user.linking_code_expires:
        return False
    if user.linking_code_expires < datetime.utcnow():
        return False

    user.telegram_chat_id = telegram_chat_id
    user.telegram_username = telegram_username
    user.bot_linked = True
    user.linking_code = None
    user.linking_code_expires = None
    db.session.commit()
    return True
