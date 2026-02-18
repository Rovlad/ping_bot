import uuid

import click
from flask import Flask
from dotenv import load_dotenv

from app.extensions import db, login_manager
from app.models import User

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, uuid.UUID(user_id))

    # Register blueprints
    from app.auth import auth_bp
    from app.dashboard import dashboard_bp
    from app.messages import messages_bp
    from app.schedules import schedules_bp
    from app.stats import stats_bp
    from app.settings import settings_bp
    from app.telegram.webhook import webhook_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(schedules_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(webhook_bp)

    # Start scheduler
    from app.scheduler.jobs import init_scheduler
    init_scheduler(app)

    # CLI commands
    @app.cli.command('db-init')
    def db_init():
        """Create all database tables."""
        db.create_all()
        print('Database tables created.')

    @app.cli.command('register-webhook')
    def register_webhook():
        """Register the Telegram webhook URL."""
        import requests
        token = app.config['TELEGRAM_BOT_TOKEN']
        url = f"{app.config['APP_URL']}/webhook/telegram"
        secret = app.config['TELEGRAM_WEBHOOK_SECRET']
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json={'url': url, 'secret_token': secret}
        )
        data = resp.json()
        if data.get('ok'):
            print(f'Webhook registered: {url}')
        else:
            print(f'Error: {data}')

    @app.cli.command('test-send')
    @click.argument('user_id')
    def test_send(user_id):
        """Send a test message to a user for debugging."""
        from app.telegram.bot import send_test_message
        user = db.session.get(User, uuid.UUID(user_id))
        if not user:
            print(f'User {user_id} not found.')
            return
        if not user.bot_linked:
            print(f'User {user.email} has not linked Telegram.')
            return
        send_test_message(user)
        print(f'Test message sent to {user.email}.')

    return app
