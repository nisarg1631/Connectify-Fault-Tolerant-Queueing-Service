import threading
from typing import Dict, List, Optional, Tuple
import uuid
import time

from src.models import Topic, Log
from src import db, app
from src import TopicDB, ConsumerDB, LogDB


class MasterQueue:
    """
    Master queue is a collection of all the topics.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._topics: Dict[(str,int), Topic] = {}

    def init_from_db(self) -> None:
        """Initialize the master queue from the db."""
        topics = TopicDB.query.all()
        for topic in topics:
            length = LogDB.query.filter_by(topic_name = topic.name, partition_index = topic.partition_index).count()
            self._topics[(topic.name,topic.partition_index)] = Topic(topic.name, topic.partition_index, length)
            # get consumers with topic_name=topic.name
            consumers = ConsumerDB.query.filter_by(topic_name=topic.name, partition_index = topic.partition_index ).all()
            for consumer in consumers:
                self._topics[(topic.name,topic.partition_index)].add_consumer(
                    consumer.id, topic.partition_index, consumer.offset
                )
            # get logs with topic_name=topic.name and ordered by their ids - deprecated
            # no longer storing logs in memory
            # logs = (
            #     LogDB.query.filter_by(topic_name=topic.name,partition_index = topic.partition_index)
            #     .order_by(LogDB.id)
            #     .all()
            # )
            # for log in logs:
            #     self._topics[(topic.name,topic.partition_index)].add_log(
            #         Log(log.producer_id, log.message, log.timestamp)
            #     )

    def _contains(self, topic_name: str, partition_index: int) -> bool:
        """Return whether the master queue contains the given topic."""
        with self._lock:
            return (topic_name,partition_index) in self._topics

    def add_topic(self, topic_name: str, partition_index:int) -> None:
        """Add a topic to the master queue."""
        with self._lock:
            self._topics[(topic_name,partition_index)] = Topic(topic_name, partition_index)

        # add to db
        db.session.add(TopicDB(name=topic_name, partition_index = partition_index))
        db.session.commit()

    def get_size(self, consumer_id: str, topic_name: str, partition_index:int = None) -> List[Dict[str,int]]:
        """Return the number of log messages in the requested partition for
        this consumer. If only topic is specified and no partition, return the 
        total number of messages in all partitions."""
        if partition_index is None:
            sizes: List[Dict[str,int]] = []
            partitions = [tuple[1] for tuple in self._topics.keys() if tuple[0] == topic_name]
            for p in partitions:
                sizes.append(self.get_size_of_partition(consumer_id, topic_name, p))
            return sizes
        return [self.get_size_of_partition(consumer_id, topic_name, partition_index)]

    def get_size_of_partition(self, consumer_id: str, topic_name: str, partition_index: int) -> Dict[str,int]:
        """
        Return the number of log messages in the requested partition for
        this consumer.
        """
        total_length = self._topics[(topic_name,partition_index)].get_length()
        consumer_offset = self._topics[(topic_name,partition_index)].get_consumer_offset(consumer_id, partition_index)
        return {"partition_number": partition_index, "size": total_length - consumer_offset}

    def get_log(self, topic_name: str, partition_index: int, consumer_id: str) -> str:
        """Return the log if consumer registered with topic and has a log
        available to pull."""
        current_length = self._topics[(topic_name, partition_index)].get_length()
        index_to_fetch = self._topics[(topic_name, partition_index)].get_and_increment_consumer_offset(consumer_id, partition_index, current_length)
        if index_to_fetch == current_length:
            return None

        # db update with index_to_fetch + 1
        db.session.execute(
            f"""
            UPDATE consumer 
            SET "offset" = GREATEST("offset", {index_to_fetch + 1}) 
            where id = '{consumer_id}' and partition_index = '{partition_index}'
            """
        )
        db.session.commit()
        return self._topics[(topic_name, partition_index)].get_log(index_to_fetch)

    def add_log(self, topic_name: str, partition_index:int, producer_id: str, message: str) -> None:
        """Add a log to the topic"""
        timestamp = time.time()

        # no longer storing logs in memory
        # index = self._topics[(topic_name,partition_index)].add_log(
        #     Log(producer_id, message, timestamp)
        # )

        index = self._topics[(topic_name,partition_index)].increment_length()

        # add to db
        db.session.add(
            LogDB(
                id=index,
                topic_name=topic_name,
                partition_index=partition_index,
                producer_id=producer_id,
                message=message,
                timestamp=timestamp,
            )
        )
        db.session.commit()

    def get_topics(self) -> List[Tuple[str,int]]:
        """Return the topic names."""
        with self._lock:
            return list(self._topics.keys())

    def add_consumer(self, topic_name: str, partition_index:int, consumer_id: str) -> None:
        """Add a consumer to the topic"""
        self._topics[(topic_name,partition_index)].add_consumer(consumer_id, partition_index)
        # add to db
        db.session.add(
            ConsumerDB(id=consumer_id, topic_name=topic_name, partition_index = partition_index,offset=0)
        )
        db.session.commit()
