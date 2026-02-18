from datetime import datetime, timedelta
from collections import defaultdict

from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract

from app.stats import stats_bp
from app.extensions import db
from app.models import SentMessage, Message


@stats_bp.route('/')
@login_required
def index():
    return render_template('stats/index.html')


@stats_bp.route('/api/overview')
@login_required
def api_overview():
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    user_id = current_user.id

    total_sent = SentMessage.query.filter(
        SentMessage.user_id == user_id,
        SentMessage.sent_at >= since,
    ).count()

    total_responded = SentMessage.query.filter(
        SentMessage.user_id == user_id,
        SentMessage.sent_at >= since,
        SentMessage.status == 'responded',
    ).count()

    response_rate = round((total_responded / total_sent * 100), 1) if total_sent > 0 else 0

    # Average response time in minutes
    responded_msgs = SentMessage.query.filter(
        SentMessage.user_id == user_id,
        SentMessage.sent_at >= since,
        SentMessage.status == 'responded',
        SentMessage.responded_at.isnot(None),
    ).all()

    if responded_msgs:
        total_mins = sum(
            (m.responded_at - m.sent_at).total_seconds() / 60 for m in responded_msgs
        )
        avg_response_time = round(total_mins / len(responded_msgs), 1)
    else:
        avg_response_time = 0

    return jsonify({
        "total_sent": total_sent,
        "total_responded": total_responded,
        "response_rate": response_rate,
        "avg_response_time_minutes": avg_response_time,
    })


@stats_bp.route('/api/response-over-time')
@login_required
def api_response_over_time():
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    user_id = current_user.id

    sent_msgs = SentMessage.query.filter(
        SentMessage.user_id == user_id,
        SentMessage.sent_at >= since,
    ).all()

    sent_by_date = defaultdict(int)
    responded_by_date = defaultdict(int)

    for m in sent_msgs:
        d = m.sent_at.strftime('%Y-%m-%d')
        sent_by_date[d] += 1
        if m.status == 'responded':
            responded_by_date[d] += 1

    # Generate all dates in range
    labels = []
    current = since.date()
    end = datetime.utcnow().date()
    while current <= end:
        labels.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    return jsonify({
        "labels": labels,
        "sent": [sent_by_date.get(d, 0) for d in labels],
        "responded": [responded_by_date.get(d, 0) for d in labels],
    })


@stats_bp.route('/api/response-distribution')
@login_required
def api_response_distribution():
    user_id = current_user.id

    messages = Message.query.filter_by(user_id=user_id).all()
    result = []

    for msg in messages:
        sent_msgs = SentMessage.query.filter(
            SentMessage.message_id == msg.id,
            SentMessage.status == 'responded',
        ).all()

        responses = defaultdict(int)
        for sm in sent_msgs:
            if sm.response:
                responses[sm.response] += 1

        if responses:
            result.append({
                "title": msg.title,
                "responses": dict(responses),
            })

    return jsonify({"messages": result})


@stats_bp.route('/api/activity-heatmap')
@login_required
def api_activity_heatmap():
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    user_id = current_user.id

    sent_msgs = SentMessage.query.filter(
        SentMessage.user_id == user_id,
        SentMessage.status == 'responded',
        SentMessage.responded_at.isnot(None),
        SentMessage.responded_at >= since,
    ).all()

    # heatmap[day_of_week][hour] = count
    heatmap = defaultdict(lambda: defaultdict(int))
    for m in sent_msgs:
        dow = m.responded_at.weekday()  # 0=Mon, 6=Sun
        hour = m.responded_at.hour
        heatmap[dow][hour] += 1

    data = []
    for dow in range(7):
        for hour in range(24):
            count = heatmap[dow][hour]
            if count > 0:
                data.append({"day": dow, "hour": hour, "count": count})

    return jsonify({"data": data})
