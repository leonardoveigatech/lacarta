import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY deve ter pelo menos 32 caracteres.")

SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_LIFETIME_MINUTES = int(os.getenv("SESSION_LIFETIME_MINUTES", "480"))
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000

SMTP_CONFIG = {
    "host": os.getenv("SMTP_HOST"),
    "port": int(os.getenv("SMTP_PORT", "587")),
    "username": os.getenv("SMTP_USER"),
    "password": os.getenv("SMTP_PASSWORD"),
    "from_email": os.getenv("SMTP_FROM_EMAIL"),
    "from_name": os.getenv("SMTP_FROM_NAME", "La Carta"),
    "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
}
