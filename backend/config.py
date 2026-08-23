import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost:3306/horarios_control",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    TIMEZONE = "America/Guatemala"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "horarios_session")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(2 * 1024 * 1024)))
    CSRF_PROTECT = os.getenv("CSRF_PROTECT", "true").lower() == "true"
    APP_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")
    BIOMETRIC_AGENT_TOKEN = os.getenv("BIOMETRIC_AGENT_TOKEN", "")
    FINGERPRINT_PROVIDER = os.getenv("FINGERPRINT_PROVIDER", "mock")
    ZKTECO_DEVICE_INDEX = int(os.getenv("ZKTECO_DEVICE_INDEX", "0"))
    ZKTECO_CAPTURE_TIMEOUT_SECONDS = int(os.getenv("ZKTECO_CAPTURE_TIMEOUT_SECONDS", "30"))
    ZKTECO_ENROLL_SAMPLES = int(os.getenv("ZKTECO_ENROLL_SAMPLES", "3"))
    ZKTECO_MATCH_THRESHOLD = int(os.getenv("ZKTECO_MATCH_THRESHOLD", "1"))
