class Config:
    """Base config."""


class ProdConfig(Config):
    FLASK_ENV = "production"
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://postgres:postgres@prime_datadb:5432/prime_datadb"
    )
    DEBUG = False
    TESTING = False


class DevConfig(Config):
    FLASK_ENV = "development"
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://postgres:postgres@prime_datadb:5432/prime_datadb"
    )
    DEBUG = True
    TESTING = True