from src import db, app, os
from src import LogDB
from typing import List
from pysyncobj import SyncObj, SyncObjConf, replicated_sync

HOSTNAME = os.environ["HOSTNAME"]

class Topic(SyncObj):
    """
    A topic is a collection of log messages that are related to each other.
    """

    def __init__(self, name: str, partition_index: int, other_brokers : List[str], my_broker : str):
        super(Topic,self).__init__(selfNode = my_broker,
                                   otherNodes = other_brokers,
                                   conf = SyncObjConf(
                                    journalFile=f"journal/ptn-{name}-{partition_index}.journal",
                                    appendEntriesUseBatch=False)
                                  )
        self._name : str = name
        self._partition_index : int = partition_index
        self.waitBinded()
        self.waitReady()

    @replicated_sync(timeout=10)
    def add_log(self, log_index: int, producer_id: str, message: str, timestamp:float) -> None:
        with app.app_context(): 
            # db.session.add(
            #     LogDB(
            #         id=log_index,
            #         topic_name=self._name,
            #         partition_index=self._partition_index,
            #         producer_id=producer_id,
            #         message=message,
            #         timestamp=timestamp,
            #     )
            # )
            db.session.execute(f'INSERT INTO log ( id, topic_name, partition_index, producer_id, message, timestamp) VALUES ({log_index},\'{self._name}\',{self._partition_index},\'{producer_id}\',\'{message}\', {timestamp}) ON CONFLICT (id, topic_name, partition_index) DO NOTHING;')
            db.session.commit()
            



    
    