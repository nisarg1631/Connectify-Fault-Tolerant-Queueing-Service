import os

class Config:
    """Base config."""

db_name = os.environ["DB_NAME"]

class ProdConfig(Config):
    FLASK_ENV = "production"
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://postgres:postgres@{db_name}:5432/{db_name}"
    )
    DEBUG = False
    TESTING = False


class DevConfig(Config):
    FLASK_ENV = "development"
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://postgres:postgres@{db_name}:5432/{db_name}"
    )
    DEBUG = True
    TESTING = True