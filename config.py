import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    _key_file = os.path.join(BASE_DIR, ".secret_key")
    if os.path.exists(_key_file):
        with open(_key_file) as f:
            SECRET_KEY = f.read().strip()
    else:
        SECRET_KEY = secrets.token_hex(32)
        with open(_key_file, "w") as f:
            f.write(SECRET_KEY)

API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "https://admin.berufswahlportal.ch/wp-json/biz/v1",
)

DATABASE = os.path.join(DATA_DIR, os.environ.get("DATABASE_FILE", "schnupper_tracker.db"))
PROFESSIONS_CACHE = os.path.join(DATA_DIR, "professions_cache.json")

DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"

CACHE_DURATION = int(os.environ.get("CACHE_DURATION", "86400"))
RESULT_CACHE_TTL = int(os.environ.get("RESULT_CACHE_TTL", "300"))

SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "schnupper_session")
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
PERMANENT_SESSION_LIFETIME = 86400
