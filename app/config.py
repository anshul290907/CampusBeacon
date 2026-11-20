import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = os.getenv("VERCEL") == "1"

DATABASE_URL = os.getenv("DATABASE_URL")
if IS_VERCEL and (not DATABASE_URL or DATABASE_URL.startswith("sqlite:")):
    # Vercel's application directory is read-only; SQLite can only be temporary there.
    DATABASE_URL = "sqlite:////tmp/campusradar.db"
elif not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{BASE_DIR / 'instance' / 'campusradar.db'}"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
