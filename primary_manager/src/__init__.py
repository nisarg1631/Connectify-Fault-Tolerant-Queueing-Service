from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import requests

from src.json_validator import expects_json
from src.async_requests import AsyncRequests
from src.sync_utils import sync_broker_metadata
from time import sleep
import config
import os
import threading

app = Flask(__name__)
app.config.from_object(config.DevConfig)

db = SQLAlchemy(app)
from db_models import *

from src.models import DataManager

data_manager = DataManager()

def health_check():
    with app.app_context():
        while True:
            brokers = data_manager.get_brokers()
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
        print("\033[94mTesting mode detected \033[0m")
        db.drop_all()
        print("\033[94mAll tables dropped.\033[0m")
    
    print("\033[94mCreating all tables...\033[0m")
    db.create_all()
    print("\033[94mAll tables created.\033[0m")
    # db.session.add(BrokerDB(name = 'broker-1'))
    # db.session.add(BrokerDB(name = 'broker-2'))
    # db.session.add(BrokerDB(name = 'broker-3'))
    # db.session.commit()
    # print("\033[94mBrokers Added.\033[0m")
    print("\033[94mInitializing master queue from database...\033[0m")
    data_manager.init_from_db()
    print("\033[94mMaster queue initialized from database.\033[0m")

    print("\033[94mStarting health check manager...\033[0m")
    threading.Thread(target=health_check).start()

    # print the master queue for debugging purposes
    if app.config["FLASK_ENV"] == "development":
        print("Active brokers in manager:")
        print(data_manager._active_brokers)
        print("Inactive brokers in manager:")
        print(data_manager._inactive_brokers)
    