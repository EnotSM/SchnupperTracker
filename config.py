import secrets
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = secrets.token_hex(32)
API_BASE_URL = "https://admin.berufswahlportal.ch/wp-json/biz/v1"
DATABASE = os.path.join(BASE_DIR, "schnupper_tracker.db")
PROFESSIONS_CACHE = os.path.join(BASE_DIR, "professions_cache.json")
CACHE_DURATION = 86400
RESULT_CACHE_TTL = 300
