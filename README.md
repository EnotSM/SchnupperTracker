# SchnupperTracker

[![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.1-000?logo=flask)](https://flask.palletsprojects.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Search and save Schnupperlehren & Lehrstellen in canton Zürich. Uses the [`berufswahl.zh.ch`](https://berufswahl.zh.ch) API.

---

## Features

- filter by type (Schnupperlehre / Lehrstelle), profession (multi-select tags), location
- profession autocomplete — filtered by selected type
- AJAX search — no full page reload
- random results when no search query (30 items)
- save / remove listings to personal list (heart icon)
- manually update status: new → sent → waiting → rejection → success
- notes on each listing (auto-save on blur / 2s idle)
- copy email / phone / website to clipboard
- open address in Google Maps
- open listing on berufswahl.zh.ch
- registration + login (session-based)
- filter saved listings by status

## Quick Start

```bash
git clone https://github.com/EnotSM/SchnupperTracker.git
cd SchnupperTracker

# nix
nix-shell

# or venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python app.py
```

Open http://localhost:5000

## Structure

```
CRUD/
├── app.py                 # routes, API, caching, security
├── config.py              # settings (secret key, session, cache)
├── requirements.txt
├── .secret_key            # auto-generated, gitignored
├── professions_cache.json # 24h API cache, gitignored
├── templates/
│   ├── base.html          # nav, flash, footer, CSP meta
│   ├── index.html         # search + results
│   ├── dashboard.html     # saved listings with statuses
│   ├── login.html
│   └── register.html
├── static/
│   ├── app.js             # all frontend logic
│   └── style.css
└── AGENTS.md              # AI assistant notes (local only)
```

## Security

- CSRF protection on all mutation endpoints (header + form field)
- Rate limiting on login (5 attempts per 5 minutes per IP)
- Session cookies: `HttpOnly`, `SameSite=Lax`, signed with persisted key
- Content-Security-Policy headers
- Passwords hashed via `werkzeug.security` (pbkdf2:sha256)
- SQL injection prevented via parameterized queries
- Jinja2 auto-escape for XSS prevention

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_DEBUG` | `1` | Enable debug mode |
| `PORT` | `5000` | Server port |
| `API_BASE_URL` | `https://admin.berufswahlportal.ch/wp-json/biz/v1` | API endpoint |
| `DATABASE_FILE` | `schnupper_tracker.db` | SQLite filename |
| `CACHE_DURATION` | `86400` | Professions cache TTL (seconds) |
| `RESULT_CACHE_TTL` | `300` | In-memory result cache TTL (seconds) |
| `SESSION_COOKIE_NAME` | `schnupper_session` | Session cookie name |

## Caveats

- Tailwind via CDN (~3MB in dev, no purged build)
- No dashboard pagination (all rows loaded client-side)
- No email/notification system
- No automated tests

Not affiliated with canton Zürich. Powered by [`berufswahl.zh.ch`](https://berufswahl.zh.ch).
