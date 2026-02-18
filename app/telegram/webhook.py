from datetime import datetime

from flask import Blueprint, request, jsonify, current_app

from app.extensions import db
from app.models import SentMessage, Message
from app.telegram.linking import validate_linking_code
from app.telegram.bot import answer_callback_query, edit_message_text, edit_message_reply_markup

webhook_bp = Blueprint('webhook', __name__)


@webhook_bp.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """Handle incoming Telegram updates."""
    # Verify webhook secret if configured
    secret = current_app.config.get('TELEGRAM_WEBHOOK_SECRET')
    if secret:
        header_secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
        if header_secret != secret:
            return jsonify({"error": "unauthorized"}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": True})

    # Handle /start command (bot linking)
    if 'message' in data:
        msg = data['message']
        text = msg.get('text', '')
        chat_id = msg['chat']['id']
        username = msg['from'].get('username', '')

        if text.startswith('/start '):
            code = text.split(' ', 1)[1].strip()
            if validate_linking_code(code, chat_id, username):
                _send_reply(chat_id, "Your Telegram account has been linked to PingBot! You will now receive scheduled messages here.")
            else:
                _send_reply(chat_id, "Invalid or expired linking code. Please generate a new code from PingBot settings.")
        elif text == '/start':
            _send_reply(chat_id, "Welcome to PingBot! To link your account, go to PingBot settings and generate a linking code.")

    # Handle callback queries (button presses)
    elif 'callback_query' in data:
        callback = data['callback_query']
        callback_id = callback['id']
        callback_data = callback.get('data', '')
        chat_id = callback['message']['chat']['id']
        tg_message_id = callback['message']['message_id']

        _handle_callback(callback_id, callback_data, chat_id, tg_message_id)

    return jsonify({"ok": True})


def _handle_callback(callback_id, callback_data, chat_id, tg_message_id):
    """Process a button press callback."""
    # Format: r_<short_id>_<response_value>
    parts = callback_data.split('_', 2)
    if len(parts) < 3 or parts[0] != 'r':
        answer_callback_query(callback_id, "Invalid response.")
        return

    short_id = parts[1]
    response_value = parts[2]

    sent = SentMessage.query.filter_by(short_id=int(short_id)).first()
    if not sent:
        answer_callback_query(callback_id, "Message not found.")
        return

    if sent.status == 'responded':
        answer_callback_query(callback_id, "You already responded to this message.")
        return

    # Resolve the display label for custom options
    message = db.session.get(Message, sent.message_id)
    if message and message.response_type == 'custom' and message.custom_options:
        try:
            idx = int(response_value)
            display_response = message.custom_options[idx]
        except (ValueError, IndexError):
            display_response = response_value
    else:
        display_response = response_value

    sent.response = display_response
    sent.responded_at = datetime.utcnow()
    sent.status = 'responded'
    db.session.commit()

    # Acknowledge the callback
    answer_callback_query(callback_id, f"Recorded: {display_response}")

    # Remove buttons and update message text
    original_text = message.body if message else "Message"
    edit_message_text(chat_id, tg_message_id, f"{original_text}\n\nYou answered: *{display_response}*")
    edit_message_reply_markup(chat_id, tg_message_id)


def _send_reply(chat_id, text):
    """Quick helper to send a text reply."""
    import requests
    token = current_app.config['TELEGRAM_BOT_TOKEN']
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10,
    )
