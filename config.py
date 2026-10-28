import os
from pathlib import Path

from dotenv import load_dotenv

# Localiza o .env na raiz do projeto, independentemente
# do diretório em que a aplicação for iniciada.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def required_env(name):
    """Obtém uma variável obrigatória ou informa qual está faltando."""
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Variável de ambiente obrigatória não configurada: {name}"
        )

    return value.strip()


def env_bool(name, default="false"):
    """Converte uma variável de ambiente em booleano."""
    value = os.getenv(name, default).strip().lower()

    if value not in ("true", "false"):
        raise RuntimeError(
            f"A variável {name} deve ser 'true' ou 'false'."
        )

    return value == "true"


def env_int(name, default=None):
    """Converte uma variável de ambiente em inteiro."""
    value = os.getenv(name)

    if value is None or not value.strip():
        if default is not None:
            return default

        raise RuntimeError(
            f"Variável de ambiente obrigatória não configurada: {name}"
        )

    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(
            f"A variável {name} deve conter um número inteiro."
        ) from exc


DB_CONFIG = {
    "host": required_env("DB_HOST"),
    "port": env_int("DB_PORT", 3306),
    "user": required_env("DB_USER"),
    "password": required_env("DB_PASSWORD"),
    "database": required_env("DB_NAME"),
}

SECRET_KEY = required_env("SECRET_KEY")

if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY deve ter pelo menos 32 caracteres."
    )

SESSION_COOKIE_SECURE = env_bool(
    "SESSION_COOKIE_SECURE", "true"
)

SESSION_COOKIE_SAMESITE = "Lax"
SESSION_LIFETIME_MINUTES = env_int(
    "SESSION_LIFETIME_MINUTES", 480
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000

SMTP_CONFIG = {
    "host": os.getenv("SMTP_HOST"),
    "port": env_int("SMTP_PORT", 587),
    "username": os.getenv("SMTP_USER"),
    "password": os.getenv("SMTP_PASSWORD"),
    "from_email": os.getenv("SMTP_FROM_EMAIL"),
    "from_name": os.getenv("SMTP_FROM_NAME", "La Carta"),
    "use_tls": env_bool("SMTP_USE_TLS", "true"),
}