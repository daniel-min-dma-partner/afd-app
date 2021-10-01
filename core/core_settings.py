import os

import environ

env = environ.Env()

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

DATABASES = {
    "default": {
        # Add the docker environment SQL_ENGINE variable or for local development use sqlite3 engine
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        # Add the docker environment SQL_DATABASE variable or use the local sqlite database soruce
        "NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        # Add the docker SQL_USER environment variable or on need password for sqlite3
        "USER": os.environ.get("SQL_USER", ""),
        # Add the docker SQL_PASSWORD environment variable or on need password for sqlite3
        "PASSWORD": os.environ.get("SQL_PASSWORD", ""),
        # Add the docker SQL_HOST environment variable or on need host for sqlite3
        "HOST": os.environ.get("SQL_HOST", ""),
        # Add the docker SQL_HOST environment variable or on need port for sqlite3
        "PORT": os.environ.get("SQL_PORT", ""),
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Extra apps
    'apscheduler',
    'bootstrap4',
    # 'channels',
    'django_apscheduler',
    'django_extensions',
    'jsoneditor',
    'mathfilters',
    'rest_framework',
    'tinymce',

    # Created apps
    # 'chat',
    'libs',
    'libs.diff2htmlcompare',
    'libs.tcrm_automation',
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Global Login required
    'global_login_required.GlobalLoginRequiredMiddleware',

    # Custom Middlewares
    'main.middleware.SfdcCRUDMiddleware',
    'main.middleware.TimezoneMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    # 'DEFAULT_PERMISSION_CLASSES': (
    #     'rest_framework.permissions.IsAdminUser'
    # ),
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "main/templates",
            BASE_DIR / "libs",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # My custom context processors
                'main.context_processors.show_notifications',
            ],
        },
    },
]

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(" ")
DEBUG = int(os.environ.get("DEBUG", default=1))
SECRET_KEY = env.str('SECRET_KEY', default='django-insecure-wi5%3e1_fpxq+fm8sowdg0^(0vz*qv0oryh3ww+adav$+v$e4%')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
WSGI_APPLICATION = 'core.wsgi.application'

# Login, Views, URLs
LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ROOT_URLCONF = 'core.urls'
PUBLIC_PATHS = [
    #     # '^%s.*' % MEDIA_URL, # allow public access to any media on your application
    r'^/admin/',
    r'^/admin/login',
    r'^/login/',
    r'^/logout/',
    r'^/register/',
    r'^/release/view',
    r'^/rest/.*',
    # r'^/sfdc/authenticate/',
]
# PUBLIC_VIEWS = [
#     'main.views.LoginView',
# ]


# # For Websocket using channels package:
# ASGI_APPLICATION = "core.asgi.application"
# # Channel backing store. You have to start first your redis docker or app.
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [('localhost', 6379)],
#         },
#     },
# }

# Language
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Recomended by Heroku. This is "production" configuration.
static_dir = os.path.join(BASE_DIR, "main/static")  # Static files for development mode
jdd_static_dir = os.path.join(BASE_DIR, "libs/jdd")
jsl_static_dir = os.path.join(BASE_DIR, "libs/jdd/jsl")
jquery_timeago_dir = os.path.join(BASE_DIR, "libs/jquery-timeago")
STATICFILES_DIRS = [
    jdd_static_dir,
    jsl_static_dir,
    jquery_timeago_dir,
]

# File Upload managers
FILE_UPLOAD_HANDLERS = [
    # "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler"
]

# File storage manager
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Media files (file uploaded, etc)
# https://docs.djangoproject.com/en/3.2/ref/files/storage/#django.core.files.storage.FileSystemStorage.location
# https://docs.djangoproject.com/en/3.2/ref/settings/#media-root
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'  # It must end in a slash if set to a non-empty value.

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom configs
SALESFORCE_INSTANCE_URLS = {
    'Sandbox': 'https://test.salesforce.com',
    'Production': 'https://login.salesforce.com',
}

# TinyMCE Settings
TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 500,
    "menubar": True,
    "menu": {
        "file": {"title": "File", "items": 'preview'}
    },
    "plugins": "advlist,autolink,lists,link,image,charmap,print,preview,anchor,"
               "searchreplace,visualblocks,code,fullscreen,insertdatetime,media,table,paste,"
               "code,help,wordcount",
    "toolbar": "undo redo | formatselect | bold italic backcolor forecolor | "
               "alignleft aligncenter alignright alignjustify | "
               "bullist numlist outdent indent | removeformat | help",
}


# Json Editor
JSON_EDITOR_CSS = "https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/9.5.5/jsoneditor.css"
JSON_EDITOR_JS = "https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/9.5.5/jsoneditor.js"
JSON_EDITOR_INIT_JS = "django-jsoneditor/jsoneditor-init.js"
