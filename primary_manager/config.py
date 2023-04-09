import os

class Config:
    """Base config."""
    DB_NAME = os.environ["DB_NAME"]
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://postgres:postgres@{DB_NAME}:5432/{DB_NAME}"
    )
    REDIS_CLUSTER_NODES = [ 
        (node.split(":")[0], int(node.split(":")[1])) 
        for node in os.environ["REDIS_CLUSTER_NODES"].split(",") 
    ]

class ProdConfig(Config):
    FLASK_ENV = "production"
    DEBUG = False
    TESTING = False


class DevConfig(Config):
    FLASK_ENV = "development"
    DEBUG = True
    TESTING = True
