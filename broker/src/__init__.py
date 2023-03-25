from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from src.json_validator import expects_json
import config
import os

app = Flask(__name__)
app.config.from_object(config.DevConfig)
db = SQLAlchemy(app)

from db_models import *

from src.models import MasterQueue

master_queue = MasterQueue()

from src import views

with app.app_context():
    if app.config["TESTING"]:
        print("\033[94mTesting mode detected. Dropping all tables...\033[0m")
        db.drop_all()
        print("\033[94mAll tables dropped.\033[0m")
    
    print("\033[94mCreating all tables...\033[0m")
    db.create_all()
    print("\033[94mAll tables created.\033[0m")
