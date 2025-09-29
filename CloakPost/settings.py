"""
Django settings for CloakPost project — Render (Django + Channels) ready.
"""

from pathlib import Path
import os
import base64
from dotenv import load_dotenv

# ---------------------------------------------------------
# Base / env
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------
# Core secrets / debug / hosts
# ---------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")

# Only backend host here (no schemes). Frontend goes in CORS/CSRF below.
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,cloakpost.onrender.com"
    ).split(",")
    if h.strip()
]

# Behind Render’s proxy: trust forwarded proto/host
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# ---------------------------------------------------------
# Applications
# ---------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Realtime (WebSockets)
    "channels",

    # CORS for cross-origin SPA
    "corsheaders",

    # Project apps
    "users.apps.UsersConfig",
    "posts.apps.PostsConfig",
    "user_messages.apps.UserMessagesConfig",
    "api",
]

MIDDLEWARE = [
    # CORS must be high (before Common & CSRF)
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",

    # Static files in production
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "CloakPost.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------
# ASGI / WSGI
# ---------------------------------------------------------
WSGI_APPLICATION = "CloakPost.wsgi.application"
ASGI_APPLICATION = "CloakPost.asgi.application"

# ---------------------------------------------------------
# Database
# ---------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    try:
        import dj_database_url  # type: ignore
        DATABASES = {
            "default": dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                ssl_require=True,
            )
        }
    except Exception:
        raise RuntimeError(
            "DATABASE_URL is set but dj-database-url is not installed. "
            "Install it: pip install dj-database-url, or use discrete POSTGRES_* vars."
        )
else:
    POSTGRES_DB = os.getenv("POSTGRES_DB", "")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

    if all([POSTGRES_DB, POSTGRES_USER, POSTGRES_HOST]):
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": POSTGRES_DB,
                "USER": POSTGRES_USER,
                "PASSWORD": POSTGRES_PASSWORD,
                "HOST": POSTGRES_HOST,
                "PORT": POSTGRES_PORT,
                "OPTIONS": {"sslmode": os.getenv("DB_SSLMODE", "require")},
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

# ---------------------------------------------------------
# Password validation
# ---------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------
# I18N / TZ
# ---------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------
# Static files (WhiteNoise)
# ---------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = []
_static_dir = BASE_DIR / "static"
if _static_dir.exists():
    STATICFILES_DIRS.append(_static_dir)

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------------------------------------------------------
# Defaults / auth
# ---------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.CustomUser"

LOGIN_URL = "/users/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/users/login/"

# ---------------------------------------------------------
# AES encryption key (Base64) — required by your code
# ---------------------------------------------------------
AES_ENCRYPTION_KEY = os.getenv("AES_ENCRYPTION_KEY")
if not AES_ENCRYPTION_KEY:
    raise RuntimeError("AES_ENCRYPTION_KEY must be set in .env")

try:
    _tmp = base64.b64decode(AES_ENCRYPTION_KEY)
    if len(_tmp) != 32:
        raise ValueError
except Exception:
    raise RuntimeError("AES_ENCRYPTION_KEY must be a valid base64-encoded 32-byte key")

# ---------------------------------------------------------
# CSRF / CORS / Cookies / Security
# ---------------------------------------------------------
# Frontend SPA origin & local dev; allow extra via env if needed
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://cloakpost-zmd1.onrender.com",
    *[
        d.strip()
        for d in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if d.strip()
    ],
]

# CSRF needs full https:// URLs
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "https://cloakpost-zmd1.onrender.com",
    "https://cloakpost.onrender.com",
    *[
        d.strip()
        for d in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
        if d.strip()
    ],
]

CORS_ALLOW_CREDENTIALS = True
# Make CORS preflights predictable
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-language",
    "content-type",
    "x-csrftoken",
    "authorization",
]
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

# Cookies for cross-site requests (SPA on a different origin)
CSRF_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True

if DEBUG:
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
else:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------
# Channels (Redis) — realtime chat
# ---------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}