import pytz
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.settings import settings_bp
from app.extensions import db
from app.telegram.linking import generate_linking_code


COMMON_TIMEZONES = sorted(pytz.common_timezones)


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_timezone':
            tz = request.form.get('timezone', 'UTC')
            if tz in pytz.all_timezones:
                current_user.timezone = tz
                db.session.commit()
                flash('Timezone updated.', 'success')
            else:
                flash('Invalid timezone.', 'danger')

        elif action == 'generate_code':
            code = generate_linking_code(current_user)
            flash(f'Your linking code is: {code} — Send /start {code} to your PingBot in Telegram. Code expires in 10 minutes.', 'info')

        elif action == 'unlink_telegram':
            current_user.telegram_chat_id = None
            current_user.telegram_username = None
            current_user.bot_linked = False
            db.session.commit()
            flash('Telegram unlinked.', 'info')

        return redirect(url_for('settings.index'))

    return render_template(
        'settings/index.html',
        timezones=COMMON_TIMEZONES,
    )
