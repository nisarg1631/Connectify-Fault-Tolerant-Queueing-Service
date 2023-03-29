import time

from src import db
from src import os
from src import TopicDB, LogDB, BrokerDB
from typing import Dict, Tuple, List
from src.models import Topic

class MasterQueue:
    """
    Master queue is a controller for the database.
    """

    def __init__(self) -> None:
        self._topics : Dict[Tuple[str,int], Topic] = {}
        self._my_broker : str = os.environ["HOSTNAME"]+":5000"

    def init_from_db(self) -> None:
        topics = TopicDB.query.all()
        for topic in topics:
            brokers = [obj.broker for obj in BrokerDB.query.filter_by(name=topic.name, partition_index = topic.partition_index).all()]
            self._topics[(topic.name, topic.partition_index)] = Topic(topic.name,topic.partition_index, brokers, self._my_broker)



    def add_topic(self, topic_name: str, partition_index:int, other_brokers:List[str]) -> None:
        """Add a partition to the database."""
        
        # Create a RAFT synced Topic Object
        self._topics[(topic_name,partition_index)] = Topic(topic_name,partition_index,other_brokers, self._my_broker)

        db.session.add(TopicDB(name=topic_name, partition_index = partition_index))
        for broker in other_brokers:
            db.session.add(BrokerDB(name = topic_name, partition_index = partition_index, broker = broker))
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
        self._topics[(topic_name,partition_index)].add_log(log_index,producer_id,message,timestamp)
        
