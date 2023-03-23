import os

class Config:
    """Base config."""

write_db_name = os.environ["WRITE_DB_NAME"]
read_db_name = os.environ["READ_DB_NAME"]

class ProdConfig(Config):
    FLASK_ENV = "production"
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://postgres:postgres@{write_db_name}:5432/{write_db_name}"
    )
    SQLALCHEMY_BINDS = {
        'read': f"postgresql://postgres:postgres@{read_db_name}:5432/{write_db_name}"
    }
    DEBUG = False
    TESTING = False


class DevConfig(Config):
    FLASK_ENV = "development"
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://postgres:postgres@{write_db_name}:5432/{write_db_name}"
    )
    SQLALCHEMY_BINDS = {
        'read': f"postgresql://postgres:postgres@{read_db_name}:5432/{write_db_name}"
    }
    DEBUG = True
    TESTING = True