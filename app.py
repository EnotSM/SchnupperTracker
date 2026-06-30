import json
import os
import random
import re
import secrets
import time
import unicodedata
from functools import wraps

import requests
from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["TEMPLATES_AUTO_RELOAD"] = config.DEBUG
app.config["SESSION_COOKIE_NAME"] = config.SESSION_COOKIE_NAME
app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE
app.config["PERMANENT_SESSION_LIFETIME"] = config.PERMANENT_SESSION_LIFETIME

_result_cache = {}
_login_attempts = {}


@app.after_request
def add_security_headers(response):
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
        "style-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' https://admin.berufswahlportal.ch; "
        "form-action 'self'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'",
    )
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.before_request
def ensure_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)


@app.before_request
def cleanup_rate_limits():
    _cleanup_rate_limits()


@app.context_processor
def inject_csrf():
    return {"csrf_token": session.get("csrf_token", "")}


def csrf_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ("POST", "PATCH", "DELETE", "PUT"):
            token = (
                request.headers.get("X-CSRF-Token", "")
                or request.form.get("csrf_token", "")
            )
            if not token or token != session.get("csrf_token", ""):
                return jsonify({"error": "CSRF token missing or invalid"}), 403
        return f(*args, **kwargs)

    return decorated


def _cached(key, ttl=300):
    key = "v1_" + key
    if key in _result_cache:
        data, ts = _result_cache[key]
        if time.time() - ts < ttl:
            return data
    return None


def _set_cache(key, data):
    _result_cache["v1_" + key] = (data, time.time())


def get_db():
    if "db" not in g:
        import sqlite3

        g.db = sqlite3.connect(config.DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(_e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS saved_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            listing_id TEXT NOT NULL,
            title TEXT,
            company TEXT,
            email TEXT,
            phone TEXT,
            website TEXT,
            address TEXT,
            listing_type TEXT,
            status TEXT DEFAULT 'new',
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, listing_id)
        );
    """)
    try:
        db.execute("ALTER TABLE saved_listings ADD COLUMN muted INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE saved_listings ADD COLUMN last_updated TEXT DEFAULT ''")
    except Exception:
        pass
    db.commit()


def _rate_limit(key, max_attempts=5, window=300):
    now = time.time()
    entry = _login_attempts.get(key, [])
    entry = [t for t in entry if now - t < window]
    if len(entry) >= max_attempts:
        return False
    entry.append(now)
    _login_attempts[key] = entry
    return True


def _cleanup_rate_limits():
    now = time.time()
    for k in list(_login_attempts.keys()):
        _login_attempts[k] = [t for t in _login_attempts[k] if now - t < 300]
        if not _login_attempts[k]:
            del _login_attempts[k]


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def api_get(endpoint, params=None):
    url = f"{config.API_BASE_URL}/{endpoint}"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"error": str(e), "data": [], "total": 0, "totalPages": 0}


def load_professions():
    cache_file = config.PROFESSIONS_CACHE
    if os.path.exists(cache_file):
        try:
            age = time.time() - os.path.getmtime(cache_file)
            if age < config.CACHE_DURATION:
                with open(cache_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    data = api_get("apprenticeship-professions", {"per_page": 500})
    if "error" in data or not isinstance(data, list):
        return []
    variants = data

    data2 = api_get("professions", {"per_page": 310})
    if isinstance(data2, dict) and "error" not in data2:
        base_list = data2.get("items", [])
    elif isinstance(data2, list):
        base_list = data2
    else:
        base_list = []

    counts_by_keyword = {}
    for i in base_list:
        title = i.get("title", "")
        sd = i.get("swissdocs", [{}])[0] if i.get("swissdocs") else {}
        keyword = title.split("/")[0].strip()
        per_year = sd.get("countApprenticeshipsPerYear")
        appr = 0
        if isinstance(per_year, dict):
            vals = [v for v in per_year.values() if isinstance(v, (int, float))]
            appr = max(vals) if vals else 0
        counts_by_keyword[keyword] = {
            "trial": sd.get("countTrialApprenticeships", 0),
            "appr": appr,
        }

    result = []
    for v in variants:
        name = v.get("name", "")
        keyword = name.split("/")[0].strip()
        c = counts_by_keyword.get(keyword, {"trial": 0, "appr": 0})
        result.append({
            "id": v.get("id"),
            "name": name,
            "number": v.get("number", ""),
            "slug": v.get("slug", ""),
            "trial_count": c["trial"],
            "appr_count": c["appr"],
        })

    try:
        with open(cache_file, "w") as f:
            json.dump(result, f)
    except OSError:
        pass
    return result


def extract_keyword(title):
    if not title or not title.strip():
        return ""
    kw = title.split("/")[0].split("(")[0].strip()
    return kw if len(kw) > 2 else title.split()[0] if title.split() else title


def normalize_item(item, listing_type=""):
    addr = item.get("organization_address") or {}
    contact = item.get("contact") or {}
    street = addr.get("street", "")
    zip_code = addr.get("zip", "")
    city = addr.get("city", "")
    address_parts = [p for p in (street, f"{zip_code} {city}".strip()) if p]
    listing_url = item.get("url", "")
    if listing_url and not listing_url.startswith("http"):
        base = "https://berufswahl.zh.ch"
        listing_url = base + listing_url
    thumb_src = ""
    thumbs = item.get("profession_thumbnails")
    if isinstance(thumbs, dict):
        for size in ("sidebar", "dashboard-slide", "full"):
            html = thumbs.get(size, "")
            if html:
                m = re.search(r'src="([^"]+)"', html)
                if m:
                    thumb_src = m.group(1)
                    break
    return {
        "id": item.get("id"),
        "title": item.get("title", ""),
        "company": item.get("organization_name", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "website": contact.get("url", ""),
        "street": street,
        "zip": zip_code,
        "city": city,
        "address": ", ".join(address_parts),
        "swissdoc_title": item.get("swissdoc_title", ""),
        "canton": addr.get("canton", ""),
        "listing_url": listing_url,
        "thumb": thumb_src,
        "last_updated": item.get("last_updated", ""),
        "type": listing_type or ("schnupper" if not item.get("searchType") else "lehrstelle"),
    }


def fetch_all_items(endpoint, query, listing_type, max_items=500):
    all_raw = []
    page = 1
    max_per_page = 100 if listing_type != "schnupper" else 200
    while True:
        params = {"search": query, "per_page": max_per_page, "page": page}
        if listing_type != "schnupper":
            params["type"] = "apprenticeship"
        data = api_get(endpoint, params)
        if isinstance(data, dict):
            if "error" in data:
                return None, data
            raw = data.get("items", [])
            total_pages = data.get("totalPages", 1)
        elif isinstance(data, list):
            raw = data
            total_pages = page
        else:
            raw = []
            total_pages = page
        if not raw:
            break
        all_raw.extend(raw)
        if page >= total_pages or len(all_raw) >= max_items:
            break
        page += 1
    return all_raw, None


def filter_by_profession(items, professions):
    if not professions:
        return items
    selected = [p.strip().lower() for p in professions.split(",") if p.strip()]
    if not selected:
        return items
    return [it for it in items if it["swissdoc_title"].lower() in selected or it["title"].lower() in selected]


def filter_by_location(items, location):
    if not location:
        return items
    loc = unicodedata.normalize("NFKD", location).encode("ascii", "ignore").decode().lower()
    result = []
    for it in items:
        if it.get("canton") and (loc == "zurich" or loc == "zuerich") and it["canton"].upper() == "ZH":
            result.append(it)
            continue
        for field in (it["city"], it["address"], it["zip"]):
            if loc in unicodedata.normalize("NFKD", field).encode("ascii", "ignore").decode().lower():
                result.append(it)
                break
    return result


def search_listings(listing_type, profession, location, page=1):
    per_page = 50
    endpoint = "trial-apprenticeships" if listing_type == "schnupper" else "search"

    first_prof = ""
    if profession:
        parts = [p.strip() for p in profession.split(",") if p.strip()]
        if parts:
            first_prof = parts[0]
    keyword = extract_keyword(first_prof) if first_prof else ""
    api_query = keyword or first_prof or location

    if profession:
        raw, err = fetch_all_items(endpoint, api_query, listing_type)
        if err:
            return err
        items = [normalize_item(it, listing_type) for it in raw]
        items = filter_by_profession(items, profession)
        if location:
            items = filter_by_location(items, location)
        start = (page - 1) * per_page
        end = start + per_page
        return {
            "data": items[start:end],
            "total": len(items),
            "totalPages": max(1, (len(items) + per_page - 1) // per_page),
            "page": page,
        }

    params = {"search": api_query, "per_page": per_page, "page": page}
    if listing_type != "schnupper":
        params["type"] = "apprenticeship"

    data = api_get(endpoint, params)
    if isinstance(data, dict):
        if "error" in data:
            return data
        raw_items = data.get("items", [])
        total = data.get("total", len(raw_items))
        total_pages = data.get("totalPages", 1)
    elif isinstance(data, list):
        raw_items = data
        total = len(data)
        total_pages = 1
    else:
        raw_items = []
        total = 0
        total_pages = 1

    items = [normalize_item(it, listing_type) for it in raw_items]

    return {
        "data": items,
        "total": total,
        "totalPages": total_pages,
        "page": page,
    }


def _diversify(items, max_per_title=3):
    seen = {}
    result = []
    for it in items:
        key = it["swissdoc_title"]
        if key not in seen:
            seen[key] = 0
        if seen[key] < max_per_title:
            result.append(it)
            seen[key] += 1
    return result


def build_page_url(params_dict, page):
    params = {k: v for k, v in params_dict.items() if v}
    params["page"] = page
    return url_for("index", **params)


def get_page_window(current, total, around=2):
    if total <= 1:
        return []
    pages = []
    pages.append({"num": 1, "url": None, "active": current == 1, "type": "page"})
    if current - around > 2:
        pages.append({"type": "gap"})
    start = max(2, current - around)
    end = min(total - 1, current + around)
    for p in range(start, end + 1):
        pages.append({"num": p, "url": None, "active": p == current, "type": "page"})
    if end < total - 1:
        pages.append({"type": "gap"})
    if total > 1:
        pages.append({"num": total, "url": None, "active": current == total, "type": "page"})
    return pages


@app.route("/")
def index():
    professions = load_professions()
    results = None
    query_params = {}

    has_params = any(k in request.args for k in ("type", "profession", "location"))
    listing_type = ""
    if has_params:
        listing_type = request.args.get("type", "schnupper") if request.args.get("type") else ""
        profession = request.args.get("profession", "")
        location = request.args.get("location", "")
        try:
            page = int(request.args.get("page", 1))
        except (ValueError, TypeError):
            page = 1
        if profession or location:
            query_params = {
                "type": listing_type or "schnupper",
                "profession": profession,
                "location": location,
                "page": page,
            }
            results = search_listings(listing_type or "schnupper", profession, location, page)

    if results is None:
        def extract_items(raw, listing_type):
            if isinstance(raw, dict) and "error" not in raw:
                return [normalize_item(it, listing_type) for it in (raw.get("items") or [])]
            if isinstance(raw, list):
                return [normalize_item(it, listing_type) for it in raw]
            return []

        cache_key = listing_type or "mixed"
        cached = _cached(cache_key, config.RESULT_CACHE_TTL)
        if cached:
            results, query_params = cached
        else:
            if listing_type == "lehrstelle":
                raw = api_get("search", {"per_page": 100, "page": random.randint(1, 40), "type": "apprenticeship"})
                items = extract_items(raw, "lehrstelle")
                random.shuffle(items)
                results = {"data": items[:30], "total": 0, "totalPages": 0, "page": 1}
                query_params = {"type": "lehrstelle", "profession": "", "location": "", "page": 1}
            elif listing_type == "schnupper":
                raw = api_get("trial-apprenticeships", {"per_page": 500, "page": random.randint(1, 90)})
                items = extract_items(raw, "schnupper")
                diverse = _diversify(items, 3)
                results = {"data": diverse[:30], "total": 0, "totalPages": 0, "page": 1}
                query_params = {"type": "schnupper", "profession": "", "location": "", "page": 1}
            else:
                schnupper_raw = api_get("trial-apprenticeships", {"per_page": 500, "page": random.randint(1, 90)})
                lehr_raw = api_get("search", {"per_page": 100, "page": random.randint(1, 40), "type": "apprenticeship"})
                combined = []
                schnupper_items = extract_items(schnupper_raw, "schnupper")
                diverse = _diversify(schnupper_items, 2)
                combined.extend(diverse[:15])
                lehr_items = extract_items(lehr_raw, "lehrstelle")
                random.shuffle(lehr_items)
                combined.extend(lehr_items[:15])
                random.shuffle(combined)
                results = {
                    "data": combined,
                    "total": 0,
                    "totalPages": 0,
                    "page": 1,
                }
                query_params = {"type": "", "profession": "", "location": "", "page": 1}
            _set_cache(cache_key, (results, query_params))

    pagination = {"pages": [], "prev": None, "next": None}
    if results and not results.get("error") and results.get("totalPages", 0) > 1:
        current = results.get("page", 1)
        total = results.get("totalPages", 1)
        window = get_page_window(current, total)
        for entry in window:
            if entry["type"] == "page":
                entry["url"] = build_page_url(query_params, entry["num"])
            pagination["pages"].append(entry)
        if current > 1:
            pagination["prev"] = build_page_url(query_params, current - 1)
        if current < total:
            pagination["next"] = build_page_url(query_params, current + 1)

    saved_ids = set()
    if "user_id" in session:
        db = get_db()
        rows = db.execute(
            "SELECT listing_id FROM saved_listings WHERE user_id = ?",
            (session["user_id"],),
        ).fetchall()
        saved_ids = {str(r["listing_id"]) for r in rows}

    selected_type = query_params.get("type", "") if query_params else ""

    return render_template(
        "index.html",
        professions=professions,
        results=results,
        query_params=query_params,
        pagination=pagination,
        selected_type=selected_type,
        saved_ids=saved_ids,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("csrf_token") or request.form["csrf_token"] != session.get("csrf_token", ""):
            flash("Session expired. Please try again.")
            return render_template("register.html")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            flash("Username and password are required.")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters.")
            return render_template("register.html")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            flash("Username already taken.")
            return render_template("register.html")

        pw_hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
        db.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        if not _rate_limit(f"login:{ip}"):
            flash("Too many login attempts. Please try again later.")
            return render_template("login.html")

        if not request.form.get("csrf_token") or request.form["csrf_token"] != session.get("csrf_token", ""):
            flash("Session expired. Please try again.")
            return render_template("login.html")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_username"] = user["username"]
            session.permanent = True
            flash("Welcome back!")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    status_filter = request.args.get("status", "")
    user_id = session["user_id"]

    if status_filter:
        rows = db.execute(
            "SELECT * FROM saved_listings WHERE user_id = ? AND status = ? ORDER BY updated_at DESC",
            (user_id, status_filter),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM saved_listings WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()

    listings = [dict(r) for r in rows]
    return render_template("dashboard.html", listings=listings, current_status=status_filter)


@app.route("/api/save", methods=["POST"])
@login_required
@csrf_required
def save_listing():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    listing_id = str(data.get("id", ""))
    if not listing_id:
        return jsonify({"error": "Missing listing_id"}), 400

    db = get_db()
    user_id = session["user_id"]

    existing = db.execute(
        "SELECT id FROM saved_listings WHERE user_id = ? AND listing_id = ?",
        (user_id, listing_id),
    ).fetchone()

    if existing:
        return jsonify({"message": "Already saved", "id": existing["id"]}), 200

    address = data.get("address", "")
    db.execute(
        """INSERT INTO saved_listings
           (user_id, listing_id, title, company, email, phone, website, address, listing_type, last_updated)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            listing_id,
            data.get("title", ""),
            data.get("company", ""),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("website", ""),
            address,
            data.get("listing_type", "schnupper"),
            data.get("last_updated", ""),
        ),
    )
    db.commit()
    saved_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return jsonify({"message": "Saved!", "id": saved_id}), 201


@app.route("/api/unsave", methods=["POST"])
@login_required
@csrf_required
def unsave_listing():
    data = request.get_json() or {}
    listing_id = str(data.get("listing_id", ""))
    if not listing_id:
        return jsonify({"error": "Missing listing_id"}), 400
    db = get_db()
    db.execute(
        "DELETE FROM saved_listings WHERE user_id = ? AND listing_id = ?",
        (session["user_id"], listing_id),
    )
    db.commit()
    return jsonify({"message": "Removed"}), 200


@app.route("/api/save/<int:save_id>", methods=["DELETE"])
@login_required
@csrf_required
def remove_saved(save_id):
    db = get_db()
    user_id = session["user_id"]
    db.execute(
        "DELETE FROM saved_listings WHERE id = ? AND user_id = ?",
        (save_id, user_id),
    )
    db.commit()
    return jsonify({"message": "Removed"})


@app.route("/api/save/<int:save_id>/status", methods=["PATCH"])
@login_required
@csrf_required
def update_status(save_id):
    data = request.get_json()
    status = data.get("status", "new")
    valid = {"new", "sent", "waiting", "rejection", "success"}
    if status not in valid:
        return jsonify({"error": "Invalid status"}), 400

    db = get_db()
    user_id = session["user_id"]
    db.execute(
        "UPDATE saved_listings SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (status, save_id, user_id),
    )
    db.commit()
    return jsonify({"message": "Status updated"})


@app.route("/api/save/<int:save_id>/note", methods=["PATCH"])
@login_required
@csrf_required
def update_note(save_id):
    data = request.get_json()
    note = data.get("note", "")

    db = get_db()
    user_id = session["user_id"]
    db.execute(
        "UPDATE saved_listings SET note = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (note, save_id, user_id),
    )
    db.commit()
    return jsonify({"message": "Note saved"})


@app.route("/api/save/<int:save_id>/hide", methods=["PATCH"])
@login_required
@csrf_required
def toggle_hide(save_id):
    data = request.get_json()
    hidden = data.get("hidden", False)
    db = get_db()
    db.execute(
        "UPDATE saved_listings SET muted = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (1 if hidden else 0, save_id, session["user_id"]),
    )
    db.commit()
    return jsonify({"message": "Hidden" if hidden else "Visible"})


if __name__ == "__main__":
    with app.app_context():
        init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=config.DEBUG)
