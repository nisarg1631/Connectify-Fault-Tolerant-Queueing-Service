import os

class Config:
    """Base config."""
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
