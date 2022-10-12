import dj_database_url
import django_heroku

INSTALLED_APPS.append('whitenoise.runserver_nostatic')

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
MIDDLEWARE.insert(1, 'django_permissions_policy.PermissionsPolicyMiddleware')
MIDDLEWARE.insert(0, 'csp.middleware.CSPMiddleware')

print(MIDDLEWARE)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tcrm_db',
        'USER': 'tcrm_user',
        'PASSWORD': '7YjvxvWLC8',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Activate Django-Heroku.
django_heroku.settings(locals())

# Configure database for Heroku
prod_db = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(prod_db)

# Static file handler for Heroku
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Securities
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 15768000  # 6 months
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True

# Django CSP Configs

# - Content Security Policy
ALLOWED_SOURCES = [
    'https://code.jquery.com/',
    'https://cdnjs.cloudflare.com/',
    'ttps://code.jquery.com/',
    'https://cdn.jsdelivr.net/',
    'https://fonts.googleapis.com/',
    'https://fonts.gstatic.com/',
    'http://www.w3.org/2000/svg',
]
CSP_IMG_SRC = ["'self'", "https://stage--dma-crma-afd.herokuapp.com/"] + ALLOWED_SOURCES
CSP_STYLE_SRC = ["'self'",
                 "sha256-a89e987c3763dcd384dd799670af53fb070c604a820921197e05c058ba8bceaf",
                 'https://stage--dma-crma-afd.herokuapp.com/'] + ALLOWED_SOURCES
CSP_SCRIPT_SRC = ["'self'", 'https://stage--dma-crma-afd.herokuapp.com/'] + ALLOWED_SOURCES
CSP_FONT_SRC = ["'self'", 'https://stage--dma-crma-afd.herokuapp.com/'] + ALLOWED_SOURCES

# - Content Security Policy
CSP_INCLUDE_NONCE_IN = ['script-src']

# Django Permissions Policy Config
PERMISSIONS_POLICY = {
    "accelerometer": [],
    "ambient-light-sensor": [],
    "autoplay": [],
    "camera": [],
    "microfone": [],
    "display-capture": [],
    "document-domain": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    "interest-cohort": [],
    "magnetometer": [],
    "microphone": [],
    "midi": [],
    "payment": [],
    "usb": [],
}
