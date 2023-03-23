from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from src.json_validator import expects_json
import config
import os

app = Flask(__name__)
app.config.from_object(config.DevConfig)
db = SQLAlchemy(app)
read_engine = None
def execute_read_query(query, params = None):
    global read_engine
    return db.session.execute(query, params, bind=read_engine)

from db_models import *

from src.models import MasterQueue

master_queue = MasterQueue()

from src import views

with app.app_context():
    # support for read queries
    read_engine = db.get_engine('read')
    
    if app.config["TESTING"]:
        print("\033[94mTesting mode detected. Dropping all tables...\033[0m")
        db.drop_all()
        print("\033[94mAll tables dropped.\033[0m")
    
    print("\033[94mCreating all tables...\033[0m")
    db.create_all()
    print("\033[94mAll tables created.\033[0m")

    print("\033[94mInitializing master queue from database...\033[0m")
    master_queue.init_from_db()
    print("\033[94mMaster queue initialized from database.\033[0m")

    # print the master queue for debugging purposes
    if app.config["FLASK_ENV"] == "development":
        print("Topics in master queue:")
        print(master_queue._topics.keys())
        # for topic_name in master_queue._topics:
        #     print(topic_name)
        #     print("Logs in topic %s:" % topic_name)
        #     print(master_queue._topics[topic_name]._logs)
        #     print("Consumers in topic %s:" % topic_name)
        #     print(master_queue._topics[topic_name]._consumers)
        #     print("Producers in topic %s:" % topic_name)
        #     print(master_queue._topics[topic_name]._producers)
