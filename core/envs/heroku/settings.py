import dj_database_url
import django_heroku


INSTALLED_APPS.append('whitenoise.runserver_nostatic')

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

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
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 60
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
