import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-world-cup-prediction-change-in-production")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = [host for host in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",") if host]

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_EXTERNAL_HOSTNAME}"]
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "predictor", "dashboard",
    "tailwind", "theme",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Dakar"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ML_MODEL_PATH = BASE_DIR / "ml_model/world_cup_prediction_pipeline.pkl"
SCORE_MODEL_PATH = BASE_DIR / "ml_model/world_cup_score_pipeline.pkl"
PREPARED_DATA_PATH = PROJECT_ROOT / "data/processed/modeling_data.csv"
MODEL_METADATA_PATH = BASE_DIR / "ml_model/model_metadata.json"
FEATURE_NAMES_PATH = BASE_DIR / "ml_model/feature_names.json"
CLASS_MAPPING_PATH = BASE_DIR / "ml_model/class_mapping.json"
TEAM_MAPPING_PATH = BASE_DIR / "ml_model/team_mapping.json"
MATCH_RESULTS_PATH = PROJECT_ROOT / "data/raw/results.csv"
FIFA_RANKING_PATH = PROJECT_ROOT / "data/raw/fifa_ranking-2024-06-20.csv"
TAILWIND_APP_NAME = "theme"
TAILWIND_USE_STANDALONE_BINARY = True
