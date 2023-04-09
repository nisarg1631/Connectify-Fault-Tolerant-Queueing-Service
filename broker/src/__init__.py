from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from src.json_validator import expects_json
from queue import Queue
from typing import List
import threading
import config
import os
import logging

app = Flask(__name__)
app.config.from_object(config.DevConfig)
db = SQLAlchemy(app)
new_topics_queue = Queue(500)


from db_models import *

from src.models import MasterQueue
from src.models import Topic

master_queue = MasterQueue()

from src import views



def add_topic_global() -> None:
    """Add a partition to the database."""
    while True: 

        # Obtain relevant information
        current_topic = new_topics_queue.get()
        
        topic_name = current_topic[0]
        partition_index = current_topic[1]
        other_brokers = current_topic[2]
        port = current_topic[3]

        # Create a RAFT synced Topic Object
        other_brokers_with_ports = [master_queue.make_raft_addr(broker,port) for broker in other_brokers]
        my_broker_with_port = master_queue.make_raft_addr(master_queue._my_broker,port)
        master_queue.topics[(topic_name,partition_index)] = Topic(topic_name,partition_index,other_brokers_with_ports, my_broker_with_port)

        with app.app_context():
            db.session.add(TopicDB(name=topic_name, partition_index = partition_index))
            for broker in other_brokers:
                db.session.add(BrokerDB(name = topic_name, partition_index = partition_index, broker = broker, port = port))
            db.session.commit()

with app.app_context():
    if app.config["TESTING"]:
        print("\033[94mTesting mode detected. Dropping all tables...\033[0m")
        db.drop_all()
        print("\033[94mAll tables dropped.\033[0m")
    print("\033[94mCreating all tables...\033[0m")
    db.create_all()
    print("\033[94mAll tables created.\033[0m")
    master_queue.init_from_db()
    threading.Thread(target = add_topic_global).start()
    print("Thread started")
