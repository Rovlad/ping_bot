import uuid
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import TypeDecorator, String

from app.extensions import db


class FlexibleUUID(TypeDecorator):
    """UUID type that works with both PostgreSQL (native) and SQLite (string)."""
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(FlexibleUUID(), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    telegram_chat_id = db.Column(db.BigInteger, nullable=True)
    telegram_username = db.Column(db.String(255), nullable=True)
    bot_linked = db.Column(db.Boolean, default=False)
    linking_code = db.Column(db.String(10), nullable=True)
    linking_code_expires = db.Column(db.DateTime, nullable=True)
    timezone = db.Column(db.String(50), default='UTC')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('Message', backref='user', lazy='dynamic')
    schedules = db.relationship('Schedule', backref='user', lazy='dynamic')
    sent_messages = db.relationship('SentMessage', backref='user', lazy='dynamic')

    def get_id(self):
        return str(self.id)


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(FlexibleUUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(FlexibleUUID(), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    response_type = db.Column(db.String(20), default='yes_no')
    custom_options = db.Column(db.JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    schedules = db.relationship(
        'Schedule', backref='message', lazy='dynamic', cascade='all, delete-orphan'
    )
    sent_messages = db.relationship(
        'SentMessage', backref='message', lazy='dynamic'
    )


class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(FlexibleUUID(), primary_key=True, default=uuid.uuid4)
    message_id = db.Column(
        FlexibleUUID(), db.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False
    )
    user_id = db.Column(FlexibleUUID(), db.ForeignKey('users.id'), nullable=False)
    cron_expression = db.Column(db.String(100), nullable=False)
    timezone = db.Column(db.String(50), default='UTC')
    is_active = db.Column(db.Boolean, default=True)
    next_run_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sent_messages = db.relationship('SentMessage', backref='schedule', lazy='dynamic')

    __table_args__ = (
        db.Index('ix_schedules_next_run_at', 'next_run_at'),
    )


class SentMessage(db.Model):
    __tablename__ = 'sent_messages'

    id = db.Column(FlexibleUUID(), primary_key=True, default=uuid.uuid4)
    short_id = db.Column(db.Integer, autoincrement=True, unique=True)
    message_id = db.Column(FlexibleUUID(), db.ForeignKey('messages.id'), nullable=False)
    schedule_id = db.Column(FlexibleUUID(), db.ForeignKey('schedules.id'), nullable=True)
    user_id = db.Column(FlexibleUUID(), db.ForeignKey('users.id'), nullable=False)
    telegram_message_id = db.Column(db.BigInteger, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    response = db.Column(db.String(100), nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='sent')

    __table_args__ = (
        db.Index('ix_sent_messages_user_sent', 'user_id', 'sent_at'),
    )
