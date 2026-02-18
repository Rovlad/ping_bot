from apscheduler.schedulers.background import BackgroundScheduler
from croniter import croniter
from datetime import datetime

import pytz

from app.extensions import db
from app.models import Schedule, Message, User, SentMessage
from app.telegram.bot import send_scheduled_message

scheduler = BackgroundScheduler()


def init_scheduler(app):
    """Add the main job and start the scheduler."""
    scheduler.add_job(
        func=process_due_messages,
        trigger='interval',
        seconds=60,
        id='process_due_messages',
        kwargs={'app': app},
        replace_existing=True,
    )
    scheduler.start()


def process_due_messages(app):
    """Find all due schedules and send their messages."""
    with app.app_context():
        now = datetime.utcnow()

        due_schedules = (
            Schedule.query
            .filter(Schedule.is_active.is_(True), Schedule.next_run_at <= now)
            .join(Message)
            .filter(Message.is_active.is_(True))
            .join(User)
            .filter(User.bot_linked.is_(True))
            .all()
        )

        for schedule in due_schedules:
            try:
                message = schedule.message
                user = schedule.user

                # Create sent_message record
                sent = SentMessage(
                    message_id=message.id,
                    schedule_id=schedule.id,
                    user_id=user.id,
                    sent_at=now,
                    status='sent',
                )
                db.session.add(sent)
                db.session.flush()  # Get the short_id

                # Send via Telegram
                tg_msg_id = send_scheduled_message(user, message, sent.short_id)
                sent.telegram_message_id = tg_msg_id

                # Update next_run_at
                _update_next_run(schedule)

                db.session.commit()

            except Exception as e:
                db.session.rollback()
                # Mark as failed and still update next_run
                try:
                    _update_next_run(schedule)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                print(f"Error sending schedule {schedule.id}: {e}")


def _update_next_run(schedule):
    """Calculate and set the next_run_at based on cron expression and timezone."""
    tz = pytz.timezone(schedule.timezone)
    local_now = datetime.now(tz)
    cron = croniter(schedule.cron_expression, local_now)
    next_local = cron.get_next(datetime)
    schedule.next_run_at = next_local.astimezone(pytz.utc).replace(tzinfo=None)


def calculate_next_run(cron_expression, timezone_str='UTC'):
    """Helper to calculate next_run_at for a new/updated schedule."""
    tz = pytz.timezone(timezone_str)
    local_now = datetime.now(tz)
    cron = croniter(cron_expression, local_now)
    next_local = cron.get_next(datetime)
    return next_local.astimezone(pytz.utc).replace(tzinfo=None)
