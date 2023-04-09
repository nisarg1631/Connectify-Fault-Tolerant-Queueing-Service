import time

from src import db
from src import os
from src import TopicDB, LogDB, BrokerDB
from typing import Dict, Tuple, List
from src.models import Topic
import logging

class MasterQueue:
    """
    Master queue is a controller for the database.
    """

    def __init__(self) -> None:
        self.topics : Dict[Tuple[str,int], Topic] = {}
        self._my_broker : str = os.environ["HOSTNAME"]
    
    def make_raft_addr(self,broker:str, port:str) -> str:
        return broker+":"+port

    def init_from_db(self) -> None:
        topics = TopicDB.query.all()
        db.session.query(LogDB).delete()
        db.session.commit()
        for topic in topics:
            brokers = [self.make_raft_addr(obj.broker,obj.port) for obj in BrokerDB.query.filter_by(name=topic.name, partition_index = topic.partition_index).all()]
            port = BrokerDB.query.filter_by(name=topic.name, partition_index = topic.partition_index).first().port
            self.topics[(topic.name, topic.partition_index)] = Topic(topic.name,topic.partition_index, brokers, self.make_raft_addr(self._my_broker,port))
        

    def add_topic(self, topic_name: str, partition_index:int, other_brokers:List[str], port:str) -> None:
        """Add a partition to the database."""
        
        # Create a RAFT synced Topic Object
        other_brokers_with_ports = [self.make_raft_addr(broker,port) for broker in other_brokers]
        my_broker_with_port = self.make_raft_addr(self._my_broker,port)
        self.topics[(topic_name,partition_index)] = Topic(topic_name,partition_index,other_brokers_with_ports, my_broker_with_port)

        db.session.add(TopicDB(name=topic_name, partition_index = partition_index))
        for broker in other_brokers:
            db.session.add(BrokerDB(name = topic_name, partition_index = partition_index, broker = broker, port = port))
        db.session.commit()

    def get_log(self, topic_name: str, partition_index: int, log_index: int) -> str:
        """Return the log at given index."""
        log = LogDB.query.filter_by(
            topic_name=topic_name, partition_index=partition_index, id=log_index
        ).first()
        if log is not None:
            return log.message
        raise Exception(f"No log found with index {log_index} in topic {topic_name} - partition {partition_index}") 


    def add_log(self, log_index: int, topic_name: str, partition_index:int, producer_id: str, message: str):
        """Add a log to the partition."""
        timestamp = time.time()
        try:
            self.topics[(topic_name,partition_index)].add_log(log_index,producer_id,message,timestamp)
        except Exception as e:
            raise Exception(f"Cluster Not Available.")
        
