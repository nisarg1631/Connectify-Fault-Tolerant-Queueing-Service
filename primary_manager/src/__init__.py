from flask import Flask
from redis.cluster import ClusterNode
from time import sleep
import requests
import threading
import config
import os

from src.json_validator import expects_json

app = Flask(__name__)
app.config.from_object(config.DevConfig)

startup_nodes = [ClusterNode(ip, port) for ip, port in app.config["REDIS_CLUSTER_NODES"]]
from src.models import DataManager
data_manager = DataManager(startup_nodes)

def health_check():
    with app.app_context():
        while True:
            broker_name = data_manager.get_broker()
            if broker_name is not None:
                # make 3 attempts to check health, if all fail, deactivate broker
                # first time keep a backoff of 1 second, second time 2 seconds
                for attempt in range(1, 4):
                    try:
                        response = requests.get(f"http://{broker_name}:5000/")
                        response.raise_for_status()
                        if not data_manager.broker_is_active(broker_name):
                            app.logger.info(f"Activating broker {broker_name}.")
                            data_manager.activate_broker(broker_name)
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt == 3:
                            if data_manager.broker_is_active(broker_name):
                                app.logger.info(f"Deactivating broker {broker_name}.")
                                data_manager.deactivate_broker(broker_name)
                            break
                        sleep(attempt)
            sleep(1)
            

from src import views

with app.app_context():
    if app.config["TESTING"]:
        print("\033[94mTesting mode detected\033[0m")
        data_manager.drop_all_metadata()
        print("\033[94mAll data dropped\033[0m")

    print("\033[94mStarting health check manager...\033[0m")
    threading.Thread(target=health_check).start()
