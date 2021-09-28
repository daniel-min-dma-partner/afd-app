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