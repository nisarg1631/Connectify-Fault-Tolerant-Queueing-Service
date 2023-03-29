from src import db
from src import LogDB
from typing import List
from pysyncobj import SyncObj, replicated_sync

class Topic(SyncObj):
    """
    A topic is a collection of log messages that are related to each other.
    """

    def __init__(self, name: str, partition_index: int, other_brokers : List[str], my_broker : str):
        super(Topic,self).__init__(selfNode = my_broker,otherNodes = other_brokers)
        self._name : str = name
        self._partition_index : int = partition_index

    @replicated_sync
    def add_log(self, log_index: int, producer_id: str, message: str, timestamp:float) -> None:
        db.session.add(
            LogDB(
                id=log_index,
                topic_name=self._name,
                partition_index=self._partition_index,
                producer_id=producer_id,
                message=message,
                timestamp=timestamp,
            )
        )
        db.session.commit()


    
    