from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from src.json_validator import expects_json
import config
import os
import requests

app = Flask(__name__)
app.config.from_object(config.DevConfig)
db = SQLAlchemy(app)
from db_models import *

from src.models import ReadonlyManager

ro_manager = ReadonlyManager()

from src import views

with app.app_context():
    if app.config["TESTING"]:
        print("\033[94mTesting mode detected.\033[0m")

    # No need to create tables as primary manager must have created them already

    print("\033[94mInitializing readonly manager from database...\033[0m")
    ro_manager.init_from_db()
    print("\033[94mReadonly manager initialized from database.\033[0m")

    # print the readonly manager for debugging purposes
    if app.config["FLASK_ENV"] == "development":
        print(ro_manager._brokers_by_topic_and_ptn)
        print(ro_manager._topics)