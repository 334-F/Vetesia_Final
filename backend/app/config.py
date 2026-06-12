"""
config.py
Configuración de la aplicación Flask.
Lee variables sensibles desde .env. Hay dos perfiles: desarrollo y producción.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración base, común a todos los entornos."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")

    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "sqlite:///vetesia.db",
)
# Render usa "postgres://" para PostgreSQL, pero nosotros usaremos SQLite por simplicidad
# En desarrollo local funciona con MySQL si DATABASE_URL apunta a uno
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cambia-este-jwt-en-produccion")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_TOKEN_LOCATION = ["headers"]

    # Mail (SMTP)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@vetesia.com")

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_xxxxx")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_xxxxx")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_xxxxx")

    # Subida de archivos
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/var/vetesia/uploads")
    INVOICE_FOLDER = os.getenv("INVOICE_FOLDER", "/var/vetesia/invoices")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5500,http://localhost:8080,http://127.0.0.1:8080,http://127.0.0.1:5500").split(",")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    # En producción, todas las claves vienen del entorno y no tienen default


config_by_name = {
    "dev": DevelopmentConfig,
    "prod": ProductionConfig,
}
