"""
Centralized configuration management for the Smart Attendance System.
Loads from .env file with fallback defaults for development.
"""

import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    
    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
    STATIC_URL_PATH = '/static'
    TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), 'templates')
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://127.0.0.1:5000,http://localhost:5000').split(',')
    
    # Content Security Policy (allows static files)
    TALISMAN_CSP = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "code.jquery.com"],
        'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"],
        'font-src': ["'self'", "cdn.jsdelivr.net", "fonts.gstatic.com"],
        'img-src': ["'self'", "data:", "https:"],
        'connect-src': ["'self'", "http://127.0.0.1:5001"],
    }
    
    # Session Security
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'smart_monitoring')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_POOL_SIZE = 20
    DB_AUTOCOMMIT = False
    
    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET', 'dev-jwt-secret-change-in-production')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '2'))
    JWT_EXPIRATION_DELTA = timedelta(hours=JWT_EXPIRATION_HOURS)
    
    # Security - Rate Limiting
    RATE_LIMIT_LOGIN = os.getenv('RATE_LIMIT_LOGIN', '5/minute')
    RATE_LIMIT_API = os.getenv('RATE_LIMIT_API', '100/hour')
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # CSRF Protection
    CSRF_ENABLED = os.getenv('CSRF_ENABLED', 'True') == 'True'
    WTF_CSRF_TIME_LIMIT = None  # Disable CSRF token time expiration
    WTF_CSRF_ENABLED = CSRF_ENABLED
    
    # Email
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'your_email@gmail.com')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', 'your_app_password')
    
    # Backend API
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://127.0.0.1:5001')
    BACKEND_TIMEOUT = int(os.getenv('BACKEND_TIMEOUT', '5'))
    
    # Cache
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '600'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
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
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig
