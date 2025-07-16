import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from a .env file (if present)
load_dotenv()

class Config:
    """
    Base configuration with default settings.
    Override or extend via subclassing for different environments.
    """
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///divy.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-jwt-secret')
    # Store hours in ENV as integer; default 24
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_HOURS', '24'))
    )

    # Gemini AI
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # Google Calendar OAuth
    GOOGLE_CALENDAR_CLIENT_ID = os.getenv('GOOGLE_CALENDAR_CLIENT_ID')
    GOOGLE_CALENDAR_CLIENT_SECRET = os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET')

    # CORS
    # Comma‑separated list of allowed origins in ENV
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000'
    ).split(',')

    # Mock integrations (for demo/testing)
    MOCK_PLAID_ENABLED = os.getenv('MOCK_PLAID_ENABLED', 'True') == 'True'
    MOCK_VENMO_ENABLED = os.getenv('MOCK_VENMO_ENABLED', 'True') == 'True'


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(Config):
    DEBUG = False
