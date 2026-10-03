"""
Santé Infantile Bénin : configuration Django (moderne & sécurisée)

Tous les secrets sont lus depuis les variables d'environnement (fichier `.env`
en local, variables d'environnement Render en production). Ne committez JAMAIS
de secrets ici. Voir `.env.example` pour la liste complète des variables.
"""

import os
from pathlib import Path

import dj_database_url
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Sécurité
# ---------------------------------------------------------------------------
SECRET_KEY = config('SECRET_KEY', default='dev-insecure-key-change-me-in-production')

DEBUG = config('DEBUG', default=False, cast=bool)

# En production (Render), ajoutez votre domaine réel. `.onrender.com` est déjà
# couvert pour le déploiement standard Render.
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,testserver,.onrender.com,.e2b.app',
    cast=Csv(),
)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://*.onrender.com,https://*.e2b.app',
    cast=Csv(),
)

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Serveur de fichiers statiques en production (Render)
    'whitenoise.runserver_nostatic',

    # Apps du projet
    'accounts',
    'sante',
    'enfants',
    'conseils',
    'sib_intelligence',
    'pro',
    'rappels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # CSP + Permissions-Policy (voir santeinfantile/middleware.py)
    'santeinfantile.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'santeinfantile.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'santeinfantile.wsgi.application'

# ---------------------------------------------------------------------------
# Base de données
# ---------------------------------------------------------------------------
# En production, utilisez la variable `DATABASE_URL` (PostgreSQL). En local,
# retombe automatiquement sur SQLite.
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600,
    )
}

# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:accueil'

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Porto-Novo'
USE_I18N = True
LANGUAGES = [('fr', 'Français'), ('en', 'English')]
LOCALE_PATHS = [BASE_DIR / 'locale']
USE_TZ = True

# ---------------------------------------------------------------------------
# Fichiers statiques & médias
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Clés API & services tiers
# ---------------------------------------------------------------------------
# Assistant IA de triage (Groq)
GROQ_API_KEY = config('GROQ_API_KEY', default='')
GROQ_MODEL = config('GROQ_MODEL', default='openai/gpt-oss-20b')

# SMS / OTP (Twilio : optionnel en attendant WhatsApp Business)
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_FROM = config('TWILIO_FROM', default='')

OTP_EXPIRY_MINUTES = config('OTP_EXPIRY_MINUTES', default=10, cast=int)
OTP_MAX_ATTEMPTS = config('OTP_MAX_ATTEMPTS', default=5, cast=int)

# ---------------------------------------------------------------------------
# En-tetes de securite (production, derriere le proxy TLS de Render)
# Actifs automatiquement quand DEBUG=False. Voir .env.example.
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000 if not DEBUG else 0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = config('X_FRAME_OPTIONS', default='SAMEORIGIN')
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=not DEBUG, cast=bool)
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Origines autorisées à afficher le site dans une iframe. `'self'` en
# production ; à élargir uniquement pour un environnement d'aperçu.
CSP_FRAME_ANCESTORS = config('CSP_FRAME_ANCESTORS', default="'self'")

# Les cookies ne doivent jamais être lisibles en JavaScript ni partir vers un
# site tiers (protection CSRF de fond).
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
# Le formulaire de triage et le chat sont postés en AJAX depuis le site :
# le token doit rester lisible par le JS, d'où HttpOnly à False côté CSRF.
CSRF_COOKIE_HTTPONLY = False

# Taille maximale d'un corps de requête (limite les envois abusifs).
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 Mio
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 500

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')
