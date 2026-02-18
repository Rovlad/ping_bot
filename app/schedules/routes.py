import uuid

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from cron_descriptor import get_description

from app.schedules import schedules_bp
from app.schedules.forms import ScheduleForm
from app.extensions import db
from app.models import Message, Schedule
from app.scheduler.jobs import calculate_next_run


@schedules_bp.route('/messages/<message_id>/schedules/new', methods=['GET', 'POST'])
@login_required
def create(message_id):
    msg = Message.query.filter_by(
        id=uuid.UUID(message_id), user_id=current_user.id
    ).first_or_404()

    form = ScheduleForm()
    form.timezone.default = current_user.timezone
    if request.method == 'GET':
        form.timezone.data = current_user.timezone

    if form.validate_on_submit():
        next_run = calculate_next_run(form.cron_expression.data, form.timezone.data)
        sched = Schedule(
            message_id=msg.id,
            user_id=current_user.id,
            cron_expression=form.cron_expression.data,
            timezone=form.timezone.data,
            next_run_at=next_run,
        )
        db.session.add(sched)
        db.session.commit()
        flash('Schedule created.', 'success')
        return redirect(url_for('messages.detail', message_id=msg.id))

    return render_template(
        'schedules/form.html', form=form, message=msg, editing=False
    )


@schedules_bp.route('/schedules/<schedule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(schedule_id):
    sched = Schedule.query.filter_by(
        id=uuid.UUID(schedule_id), user_id=current_user.id
    ).first_or_404()
    msg = sched.message

    form = ScheduleForm(obj=sched)

    if form.validate_on_submit():
        sched.cron_expression = form.cron_expression.data
        sched.timezone = form.timezone.data
        sched.next_run_at = calculate_next_run(form.cron_expression.data, form.timezone.data)
        db.session.commit()
        flash('Schedule updated.', 'success')
        return redirect(url_for('messages.detail', message_id=msg.id))

    return render_template(
        'schedules/form.html', form=form, message=msg, editing=True, schedule=sched
    )


@schedules_bp.route('/schedules/<schedule_id>/toggle', methods=['POST'])
@login_required
def toggle(schedule_id):
    sched = Schedule.query.filter_by(
        id=uuid.UUID(schedule_id), user_id=current_user.id
    ).first_or_404()
    sched.is_active = not sched.is_active
    if sched.is_active:
        sched.next_run_at = calculate_next_run(sched.cron_expression, sched.timezone)
    db.session.commit()

    if request.headers.get('HX-Request'):
        cron_desc = _safe_cron_desc(sched.cron_expression)
        return render_template(
            'schedules/_schedule_row.html', sched=sched, cron_desc=cron_desc
        )

    flash(f'Schedule {"activated" if sched.is_active else "paused"}.', 'info')
    return redirect(url_for('messages.detail', message_id=sched.message_id))


@schedules_bp.route('/schedules/<schedule_id>/delete', methods=['POST'])
@login_required
def delete(schedule_id):
    sched = Schedule.query.filter_by(
        id=uuid.UUID(schedule_id), user_id=current_user.id
    ).first_or_404()
    message_id = sched.message_id
    db.session.delete(sched)
    db.session.commit()

    if request.headers.get('HX-Request'):
        return ''

    flash('Schedule deleted.', 'success')
    return redirect(url_for('messages.detail', message_id=message_id))


def _safe_cron_desc(cron_expr):
    try:
        return get_description(cron_expr)
    except Exception:
        return cron_expr
