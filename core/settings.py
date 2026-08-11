"""
Django settings for core project.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / 'secrets.json') as secrets_file:
    secrets = json.load(secrets_file)

SECRET_KEY = secrets['SECRET_KEY']
DEBUG = secrets['DEBUG']
ALLOWED_HOSTS = secrets['ALLOWED_HOSTS']
SITE_URL = secrets.get('SITE_URL', 'https://store.enjaztechnology.com')

# Obscured admin path. core.middleware.AdminAccessMiddleware also gates it
# behind an existing superuser session, so even knowing this path doesn't
# expose a login form to anonymous probing.
ADMIN_URL = 'MZQ7K/'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',

    # Third-party
    'rest_framework',
    'django_filters',
    'axes',

    # Local apps
    'accounts',
    'products',
    'cart',
    'orders',
    'payments',
    'coupons',
    'dashboard',
    'pages',
    'ads',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.AdminAccessMiddleware',
    'accounts.middleware.TrackUserActivityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dashboard.middleware.ComingSoonMiddleware',
    'dashboard.middleware.VisitorTrackingMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart',
                'ads.context_processors.banners',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': secrets['DATABASE']
}

if DATABASES['default']['ENGINE'].endswith('sqlite3'):
    DATABASES['default']['NAME'] = BASE_DIR / DATABASES['default']['NAME']


# Custom user model

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'accounts.backends.EmailOrUsernameBackend',
]


# Login brute-force protection (django-axes)
# Locks out an ip+username pair after repeated failed logins instead of
# allowing unlimited password guesses.

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hour
AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']
AXES_RESET_ON_SUCCESS = True


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'ar'

TIME_ZONE = 'Africa/Khartoum'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Content-hashed filenames (e.g. favicon.3b1a2c9d.png) so browsers fetch a
# fresh copy whenever a static file's content changes, instead of serving a
# stale cached one until a hard refresh. Manifest storage only resolves
# against collectstatic's output in STATIC_ROOT, which runserver's DEBUG
# static serving never uses — so plain storage is kept for local dev, where
# {% static %} needs to resolve straight to STATICFILES_DIRS.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage' if DEBUG else
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

# Media files (user uploads: product images, etc.)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/min',
        'user': '120/min',
    },
}

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'products:list'
LOGOUT_REDIRECT_URL = 'products:list'


# Email (Namecheap Private Email — mailboxes: no-reply@, support@, info@enjaztechnology.com)

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.privateemail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 10
EMAIL_HOST_USER = secrets['EMAIL']['HOST_USER']
EMAIL_HOST_PASSWORD = secrets['EMAIL']['HOST_PASSWORD']
DEFAULT_FROM_EMAIL = 'إنجاز ستور <no-reply@enjaztechnology.com>'
SERVER_EMAIL = 'no-reply@enjaztechnology.com'
# Reply-To for outbound mail where a customer reply is expected (orders, returns,
# marketing) — no-reply@ stays the sending/authenticated address either way.
SUPPORT_EMAIL = secrets.get('SUPPORT_EMAIL', 'info@enjaztechnology.com')

ADMINS = [('Khattab', 'khattabaljaily@gmail.com')]
MANAGERS = ADMINS


# Logging
# Errors also get emailed to ADMINS (see mail_admins handler below) on top
# of the rotating file, now that SMTP is configured.

(BASE_DIR / 'logs').mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_exception': {
            '()': 'core.logging_filters.RequireExceptionInfo',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'WARNING',
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
            'filters': ['require_exception'],
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


# Transport security
# Customer data (login credentials, addresses) must travel encrypted end to
# end. Left off under DEBUG so local http:// development still works.

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
