from datetime import datetime, timedelta

from flask import render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from app.dashboard import dashboard_bp
from app.extensions import db
from app.models import Message, SentMessage


@dashboard_bp.route('/')
@login_required
def index():
    user_id = current_user.id

    # Active messages count
    active_messages = Message.query.filter_by(user_id=user_id, is_active=True).count()

    # Sent today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    sent_today = SentMessage.query.filter(
        SentMessage.user_id == user_id,
        SentMessage.sent_at >= today_start,
    ).count()

    # Response rate (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    total_7d = SentMessage.query.filter(
        SentMessage.user_id == user_id,
        SentMessage.sent_at >= seven_days_ago,
    ).count()
    responded_7d = SentMessage.query.filter(
        SentMessage.user_id == user_id,
        SentMessage.sent_at >= seven_days_ago,
        SentMessage.status == 'responded',
    ).count()
    response_rate = round((responded_7d / total_7d * 100), 1) if total_7d > 0 else 0

    # Pending responses
    pending = SentMessage.query.filter(
        SentMessage.user_id == user_id,
        SentMessage.status == 'sent',
    ).count()

    # Recent activity
    recent = (
        SentMessage.query
        .filter_by(user_id=user_id)
        .join(Message)
        .order_by(SentMessage.sent_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        'dashboard/index.html',
        active_messages=active_messages,
        sent_today=sent_today,
        response_rate=response_rate,
        pending=pending,
        recent=recent,
    )
