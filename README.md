# PingBot

A full-stack application for scheduling recurring Telegram messages with interactive response buttons (Yes/No or custom options). Includes a web dashboard for managing messages, schedules, and viewing response statistics.

## Tech Stack

- **Backend:** Python 3.11+, Flask, Flask-Login, Flask-APScheduler
- **Database:** Supabase PostgreSQL (via SQLAlchemy)
- **Frontend:** Jinja2 templates, Bootstrap 5, HTMX, Chart.js
- **Telegram:** Telegram Bot API (via `requests`)
- **Scheduler:** APScheduler (background, runs in Flask process)

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values:
#   SECRET_KEY, DATABASE_URL, TELEGRAM_BOT_TOKEN, APP_URL
```

### 3. Initialize database

```bash
flask db-init
```

### 4. Run the application

```bash
# Development
flask run

# Production (single worker for APScheduler)
gunicorn run:app --workers 1 --bind 0.0.0.0:5000
```

### 5. Register Telegram webhook

```bash
flask register-webhook
```

## Docker

```bash
docker-compose up --build
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `flask db-init` | Create all database tables |
| `flask register-webhook` | Register Telegram webhook URL with Telegram API |
| `flask test-send <user_id>` | Send a test message to a user (for debugging) |

## Architecture

```
Flask Application
├── Web Routes (Dashboard) — Jinja2 + HTMX + Bootstrap 5
├── Telegram Webhook Handler — processes /start and button callbacks
├── APScheduler (cron runner) — checks every 60s for due messages
└── Database Layer (SQLAlchemy) → Supabase PostgreSQL
```

## Features

- **User Authentication:** Sign up, log in, session management via Flask-Login
- **Telegram Bot Linking:** Generate a 6-character code, send `/start CODE` to the bot
- **Message Management:** Create messages with Yes/No or custom response buttons
- **Schedule Management:** User-friendly cron builder (Daily, Weekdays, Weekly, Monthly, Custom)
- **Auto-sending:** APScheduler sends due messages every 60 seconds
- **Response Tracking:** Button presses recorded in real-time via Telegram webhook
- **Dashboard:** Overview cards (active messages, sent today, response rate, pending)
- **Statistics:** Chart.js charts — response over time, distribution, activity heatmap
- **HTMX:** Toggle active/inactive, delete with confirmation, auto-refresh — all without page reloads

## Database Schema

- `users` — accounts with Telegram linking fields
- `messages` — scheduled message content with response type configuration
- `schedules` — cron expressions with timezone and pre-calculated next_run_at
- `sent_messages` — delivery log with response tracking

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key for sessions |
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token |
| `TELEGRAM_WEBHOOK_SECRET` | Secret for verifying webhook requests |
| `APP_URL` | Public URL of the application (for webhook registration) |

## Deployment Notes

- Use `--workers 1` with gunicorn so APScheduler runs exactly once
- Telegram webhooks require HTTPS — deploy behind a reverse proxy or use a platform that provides HTTPS
- Set `FLASK_ENV=production` and use a strong `SECRET_KEY`
- The Supabase database uses standard PostgreSQL — no special configuration needed
