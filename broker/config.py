import os


write_db_name = os.environ["WRITE_DB_NAME"]

class Config:
    """Base config."""
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://postgres:postgres@{write_db_name}:5432/{write_db_name}"
    )

class ProdConfig(Config):
    FLASK_ENV = "production"
    DEBUG = False
    TESTING = False


class DevConfig(Config):
    FLASK_ENV = "development"
    DEBUG = True
    TESTING = True
