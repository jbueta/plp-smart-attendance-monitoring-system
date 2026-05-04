"""Centralized configuration management for the Smart Attendance System."""

import importlib
import os
import secrets
from datetime import timedelta


def _load_dotenv_if_available() -> bool:
    try:
        dotenv = importlib.import_module("dotenv")
    except ImportError:
        return False

    load_dotenv = getattr(dotenv, "load_dotenv", None)
    if not callable(load_dotenv):
        return False

    return bool(load_dotenv())


_load_dotenv_if_available()


def _get_bool(name: str, default: str = "False") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration shared by the frontend and backend Flask apps."""

    BASE_DIR = os.path.dirname(__file__)

    # Flask
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = _get_bool("FLASK_DEBUG")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
    STATIC_FOLDER = os.path.join(BASE_DIR, "static")
    STATIC_URL_PATH = "/static"
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")

    # Session security
    SESSION_COOKIE_SECURE = _get_bool("SESSION_COOKIE_SECURE")
    SESSION_COOKIE_HTTPONLY = _get_bool("SESSION_COOKIE_HTTPONLY", "True")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv("SESSION_LIFETIME_HOURS", "2")))

    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "smart_monitoring")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_AUTOCOMMIT = _get_bool("DB_AUTOCOMMIT")

    # Security / API
    JWT_SECRET = os.getenv("JWT_SECRET") or secrets.token_hex(32)
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "2"))
    JWT_EXPIRATION_DELTA = timedelta(hours=JWT_EXPIRATION_HOURS)
    CSRF_ENABLED = _get_bool("CSRF_ENABLED", "True")
    RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "5/minute")
    RATE_LIMIT_API = os.getenv("RATE_LIMIT_API", "100/hour")
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", "memory://")

    # CORS / integration
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5001")
    BACKEND_TIMEOUT = int(os.getenv("BACKEND_TIMEOUT", "5"))
    ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5000,http://127.0.0.1:5000",
        ).split(",")
        if origin.strip()
    ]

    # Content Security Policy
    TALISMAN_CSP = {
        "default-src": "'self'",
        "script-src": ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "code.jquery.com"],
        "style-src": ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"],
        "font-src": ["'self'", "cdn.jsdelivr.net", "fonts.gstatic.com"],
        "img-src": ["'self'", "data:", "https:"],
        "connect-src": ["'self'", BACKEND_API_URL],
    }

    # Cache
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", "600"))

    # Email
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = Config.DEBUG
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


def get_config():
    """Get appropriate configuration based on FLASK_ENV."""

    env = os.getenv("FLASK_ENV", "development").strip().lower()

    if env == "production":
        return ProductionConfig
    if env == "testing":
        return TestingConfig

    return DevelopmentConfig
