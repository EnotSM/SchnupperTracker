<div align="center">

# 🔍 SchnupperTracker

**Discover and track Swiss apprenticeship opportunities — Schnupperlehren & Lehrstellen**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)](https://www.python.org)
[![Flask 3.x](https://img.shields.io/badge/flask-3.x-000?logo=flask)](https://flask.palletsprojects.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Search, save, filter, and annotate apprenticeship listings from the canton of Zürich — all in an Excel‑like dashboard.

</div>

---

## ✨ Features

- **🔎 Smart search** — filter by type (Schnupperlehre / Lehrstelle), profession (multi‑select autocomplete), and location
- **🎲 Discover mode** — random curated results when you don't know what to search for
- **💾 Save & organize** — bookmark listings with one click, manage them in a personal dashboard
- **📊 Status tracking** — mark progress: new → sent → waiting → rejection → success
- **📝 Notes** — attach notes to each listing, auto‑saved on blur or after 2s idle
- **📋 One‑click copy** — copy email, phone, or website to clipboard
- **🗺️ Maps integration** — open any address directly in Google Maps
- **👤 User accounts** — registration + session‑based login

## 🚀 Quick Start

```bash
git clone https://github.com/EnotSM/SchnupperTracker.git
cd SchnupperTracker
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000**

> **NixOS?** Use `nix-shell` instead of venv.

## 🎮 Usage

1. Open the app in your browser
2. Select *Schnupperlehre* or *Lehrstelle*
3. Start typing a profession name and pick from the autocomplete dropdown
4. Optionally enter a location (e.g. *Zürich*, *Winterthur*)
5. Click **Search** — results load via AJAX, no page reload
6. Click the ❤️ icon to save a listing to your personal list
7. Open **My List** to manage statuses, write notes, hide, or remove entries

## 🏗️ Architecture

```
app.py                Flask routes, API client, caching, pagination
config.py             Settings (secret key, session, cache TTLs)
templates/            Jinja2 templates (base, search, dashboard, auth)
static/               Vanilla JS + CSS (Tailwind CDN)
```

The app talks to the [`berufswahl.zh.ch`](https://berufswahl.zh.ch) WordPress JSON REST API. Search results are paginated client‑side; saved listings live in a local SQLite database.

## 🛡️ Security

| Measure | Detail |
|---------|--------|
| CSRF | Token in meta tag + `X-CSRF-Token` header on all mutations |
| Rate limiting | 5 login attempts per 5 minutes per IP |
| Sessions | Signed cookies, `HttpOnly`, `SameSite=Lax` |
| Passwords | `pbkdf2:sha256` via `werkzeug.security` |
| SQL injection | Parameterized queries throughout |
| XSS | Jinja2 auto‑escape, CSP headers |
| Headers | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` |

## 🛠️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_DEBUG` | `1` | Debug mode |
| `PORT` | `5000` | Server port |
| `DATABASE_FILE` | `schnupper_tracker.db` | SQLite filename |
| `CACHE_DURATION` | `86400` | Professions cache TTL (s) |
| `RESULT_CACHE_TTL` | `300` | In‑memory result cache TTL (s) |
| `SESSION_COOKIE_NAME` | `schnupper_session` | Session cookie name |

## ⚠️ Caveats

- Tailwind loaded via CDN (~3 MB in dev, no purged build)
- Dashboard loads all rows client‑side (no server‑side pagination)
- No email or notification system
- No automated tests

## 📄 License

[MIT](LICENSE) — free to use, modify, and distribute.

---

<div align="center">
Not affiliated with the canton of Zürich. Powered by <a href="https://berufswahl.zh.ch">berufswahl.zh.ch</a>.
</div>
