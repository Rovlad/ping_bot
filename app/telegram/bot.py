import requests
from flask import current_app


def _api_url():
    token = current_app.config['TELEGRAM_BOT_TOKEN']
    return f"https://api.telegram.org/bot{token}"


def send_scheduled_message(user, message, sent_message_short_id):
    """Send a Telegram message with inline keyboard buttons.

    Uses short_id in callback_data to stay under Telegram's 64-byte limit.
    """
    # Build keyboard
    if message.response_type == 'yes_no':
        buttons = [
            [
                {"text": "Yes", "callback_data": f"r_{sent_message_short_id}_yes"},
                {"text": "No", "callback_data": f"r_{sent_message_short_id}_no"},
            ]
        ]
    else:
        options = message.custom_options or []
        buttons = [[
            {"text": opt, "callback_data": f"r_{sent_message_short_id}_{i}"}
            for i, opt in enumerate(options)
        ]]

    payload = {
        "chat_id": user.telegram_chat_id,
        "text": message.body,
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": buttons},
    }

    resp = requests.post(f"{_api_url()}/sendMessage", json=payload, timeout=10)
    data = resp.json()

    if data.get("ok"):
        return data["result"]["message_id"]
    else:
        raise Exception(f"Telegram error: {data}")


def send_test_message(user):
    """Send a simple test message to verify the bot link works."""
    payload = {
        "chat_id": user.telegram_chat_id,
        "text": "PingBot test message. Your bot link is working!",
    }
    resp = requests.post(f"{_api_url()}/sendMessage", json=payload, timeout=10)
    data = resp.json()
    if not data.get("ok"):
        raise Exception(f"Telegram error: {data}")


def answer_callback_query(callback_query_id, text=""):
    """Answer a callback query to dismiss the loading spinner."""
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    requests.post(f"{_api_url()}/answerCallbackQuery", json=payload, timeout=10)


def edit_message_text(chat_id, message_id, text):
    """Edit a message's text."""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    requests.post(f"{_api_url()}/editMessageText", json=payload, timeout=10)


def edit_message_reply_markup(chat_id, message_id, reply_markup=None):
    """Edit or remove a message's inline keyboard."""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    else:
        payload["reply_markup"] = {"inline_keyboard": []}
    requests.post(f"{_api_url()}/editMessageReplyMarkup", json=payload, timeout=10)
