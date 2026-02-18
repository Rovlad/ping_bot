import uuid
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.messages import messages_bp
from app.messages.forms import MessageForm
from app.extensions import db
from app.models import Message, SentMessage


@messages_bp.route('/')
@login_required
def list_messages():
    messages = (
        Message.query
        .filter_by(user_id=current_user.id)
        .order_by(Message.created_at.desc())
        .all()
    )
    return render_template('messages/list.html', messages=messages)


@messages_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    form = MessageForm()
    if form.validate_on_submit():
        custom_opts = None
        if form.response_type.data == 'custom' and form.custom_options_raw.data:
            custom_opts = [
                o.strip() for o in form.custom_options_raw.data.split(',') if o.strip()
            ]

        msg = Message(
            user_id=current_user.id,
            title=form.title.data,
            body=form.body.data,
            response_type=form.response_type.data,
            custom_options=custom_opts,
        )
        db.session.add(msg)
        db.session.commit()
        flash('Message created.', 'success')
        return redirect(url_for('messages.detail', message_id=msg.id))

    return render_template('messages/form.html', form=form, editing=False)


@messages_bp.route('/<message_id>')
@login_required
def detail(message_id):
    msg = Message.query.filter_by(
        id=uuid.UUID(message_id), user_id=current_user.id
    ).first_or_404()

    schedules = msg.schedules.order_by(None).all()
    history = (
        SentMessage.query
        .filter_by(message_id=msg.id)
        .order_by(SentMessage.sent_at.desc())
        .limit(50)
        .all()
    )

    return render_template(
        'messages/detail.html', message=msg, schedules=schedules, history=history
    )


@messages_bp.route('/<message_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(message_id):
    msg = Message.query.filter_by(
        id=uuid.UUID(message_id), user_id=current_user.id
    ).first_or_404()

    form = MessageForm(obj=msg)
    if request.method == 'GET' and msg.custom_options:
        form.custom_options_raw.data = ', '.join(msg.custom_options)

    if form.validate_on_submit():
        msg.title = form.title.data
        msg.body = form.body.data
        msg.response_type = form.response_type.data
        if form.response_type.data == 'custom' and form.custom_options_raw.data:
            msg.custom_options = [
                o.strip() for o in form.custom_options_raw.data.split(',') if o.strip()
            ]
        else:
            msg.custom_options = None
        db.session.commit()
        flash('Message updated.', 'success')
        return redirect(url_for('messages.detail', message_id=msg.id))

    return render_template('messages/form.html', form=form, editing=True, message=msg)


@messages_bp.route('/<message_id>/toggle', methods=['POST'])
@login_required
def toggle(message_id):
    msg = Message.query.filter_by(
        id=uuid.UUID(message_id), user_id=current_user.id
    ).first_or_404()
    msg.is_active = not msg.is_active
    db.session.commit()

    if request.headers.get('HX-Request'):
        return render_template('messages/_message_row.html', msg=msg)

    flash(f'Message {"activated" if msg.is_active else "deactivated"}.', 'info')
    return redirect(url_for('messages.list_messages'))


@messages_bp.route('/<message_id>/delete', methods=['POST'])
@login_required
def delete(message_id):
    msg = Message.query.filter_by(
        id=uuid.UUID(message_id), user_id=current_user.id
    ).first_or_404()
    db.session.delete(msg)
    db.session.commit()

    if request.headers.get('HX-Request'):
        return ''  # Row removed

    flash('Message deleted.', 'success')
    return redirect(url_for('messages.list_messages'))
