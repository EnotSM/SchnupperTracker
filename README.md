# SchnupperTracker

> Find and track apprenticeships (Schnupperlehren & Lehrstellen) in canton Zürich.

A Flask web app that searches the [`berufswahl.zh.ch`](https://berufswahl.zh.ch) API, lets you save interesting listings, and track your application status.

![Python](https://img.shields.io/badge/python-3.11-teal?style=flat)
![Flask](https://img.shields.io/badge/flask-3.1-gray?style=flat)
![Tailwind CSS](https://img.shields.io/badge/tailwind_css-CDN-38bdf8?style=flat)

---

## Features

- **Search** — filter by type (Schnupperlehre / Lehrstelle), profession (multi-select), and location
- **Discover** — random results when no search query is entered
- **Save** — bookmark listings to your personal list
- **Track** — update status (new → sent → waiting → rejection → success)
- **Notes** — add private notes to each listing
- **Mute** — dim listings you're no longer interested in

## Quick Start

```bash
# Clone
git clone https://github.com/EnotSM/SchnupperTracker.git
cd SchnupperTracker

# Option A: Nix
nix-shell

# Option B: venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python app.py
```

Open http://localhost:5000

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11, Flask, SQLite |
| Frontend | Jinja2, Tailwind CSS (CDN), Vanilla JS |
| API | `admin.berufswahlportal.ch/wp-json/biz/v1` |
| Auth | Session-based, Werkzeug password hashing |
| Dev | Nix shell / venv |

## Project Structure

```
CRUD/
├── app.py                    # Routes, API logic, caching
├── config.py                 # App configuration
├── templates/
│   ├── base.html             # Layout (nav, flash, footer)
│   ├── index.html            # Main search page
│   ├── login.html
│   ├── register.html
│   └── dashboard.html        # Saved listings (CRUD)
├── static/
│   ├── app.js                # All frontend logic
│   └── style.css             # Custom styles
└── AGENTS.md                 # AI assistant docs
```

## Caching

- **Professions** — file cache (`professions_cache.json`), TTL: 24h
- **Random results** — in-memory cache (`_result_cache`), TTL: 5 min
- **API timeout** — 8 seconds

## License

Not affiliated with canton Zürich. Powered by [`berufswahl.zh.ch`](https://berufswahl.zh.ch).
