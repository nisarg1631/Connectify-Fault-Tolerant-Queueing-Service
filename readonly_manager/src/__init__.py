from flask import Flask
from redis.cluster import ClusterNode
from src.json_validator import expects_json
import config
import os
import requests

app = Flask(__name__)
app.config.from_object(config.DevConfig)

startup_nodes = [ClusterNode(ip, port) for ip, port in app.config["REDIS_CLUSTER_NODES"]]
from src.models import ReadonlyManager
ro_manager = ReadonlyManager(startup_nodes)

from src import views
