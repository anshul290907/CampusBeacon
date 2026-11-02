import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-me')

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f"sqlite:///{BASE_DIR / 'instance' / 'campusradar.db'}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'

    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')

    ALLOWED_EMAIL_DOMAINS = [
        x.strip().lower()
        for x in os.getenv('ALLOWED_EMAIL_DOMAINS', '').split(',')
        if x.strip()
    ]