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
├── app.py                 # routes, API, caching
├── config.py              # settings
├── templates/
│   ├── base.html          # nav, flash, footer
│   ├── index.html         # search + results
│   ├── dashboard.html     # saved listings with statuses
│   ├── login.html
│   └── register.html
├── static/
│   ├── app.js             # all frontend logic
│   └── style.css
└── AGENTS.md              # AI assistant docs
```

## API Routes

| Route | Description |
|-------|-------------|
| `POST /api/save` | save a listing |
| `POST /api/unsave` | remove by listing_id |
| `DELETE /api/save/<id>` | remove by DB id |
| `PATCH /api/save/<id>/status` | update status |
| `PATCH /api/save/<id>/note` | update note |

## Caveats

- `SECRET_KEY` is generated on every start — sessions reset on restart
- debug mode on, no CSRF
- professions cached to file for 24 hours
- random results cached in memory for 5 minutes
- API timeout: 8 seconds

Not affiliated with canton Zürich. Powered by [`berufswahl.zh.ch`](https://berufswahl.zh.ch).
