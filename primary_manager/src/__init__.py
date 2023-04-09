from flask import Flask
from flask_sqlalchemy import SQLAlchemy
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
            # broker health - 0 means healthy, for every failue
            # increment by 1, when counter reaches -3, mark broker
            # as inactive
            # brokers = data_manager.get_brokers()
            brokers = [] # TODO: reimplement healthcheck using REDIS structures
            for broker in brokers:
                try:
                    response = requests.get(f"http://{broker}:5000/")
                    response.raise_for_status()

                    app.logger.info(f"Resetting broker health of {broker}.")
                    old_health = data_manager.reset_broker_health(broker)
                    # activate broker if previously inactive
                    if old_health == -3:
                        try:
                            app.logger.info(f"Activating broker {broker}.")
                            data_manager.activate_broker(broker)
                        except Exception as e:
                            app.logger.warning(str(e))
                
                except requests.exceptions.RequestException as e:
                    app.logger.info(f"Decrementing broker health of {broker}.")
                    old_health = data_manager.decrement_broker_health(broker)
                    # deactivate broker if failed thrice
                    if old_health == -2:
                        try:
                            app.logger.info(f"Deactivating broker {broker}.")
                            data_manager.deactivate_broker(broker)
                        except Exception as e:
                            app.logger.warning(str(e))
                            
            # check every 1 second
            sleep(1)

from src import views

with app.app_context():
    if app.config["TESTING"]:
        print("\033[94mTesting mode detected\033[0m")
        data_manager.drop_all_metadata()
        print("\033[94mAll data dropped\033[0m")

    print("\033[94mStarting health check manager...\033[0m")
    threading.Thread(target=health_check).start()
