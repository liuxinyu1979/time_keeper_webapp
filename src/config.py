from datetime import timedelta

class Config(object):
    pass

class ProdConfig(Config):
    pass

class DevConfig(Config):
    time_keeper_db_name = "testtimedb"
    # time_keeper_db_name = "timedb"
    MONGO_URI = f"mongodb://localhost:27017/{time_keeper_db_name}"
    MONGODB_CONNECTION_TIMEOUT_MS = 100
    # python -c 'import secrets; print(secrets.token_hex())'
    SECRET_KEY = "my secret key"
    # maximum file size 20MB
    MAX_CONTENT_LENGTH = 1024 * 1024 * 20
    UPLOAD_EXTENSIONS = ['.csv']
    # Allow relogin after 30 minutes
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    DEBUG=True

class TestingConfig(Config):
    TESTING = True
