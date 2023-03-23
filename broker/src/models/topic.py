import threading

from src.datastructures import (
    ThreadSafeLogQueue,
    ThreadSafeConsumerDict,
    ThreadSafeProducerSet,
)
from src.models import Log
from src import execute_read_query

class Topic:
    """
    A topic is a collection of log messages that are related to each other.
    """

    def __init__(self, name: str, partition_index: int, length: int = 0):
        self._name = name
        self._partition_index = partition_index
        # self._logs = ThreadSafeLogQueue() # deprecated - no longer storing logs in memory
        self._len = length # counter of logs inserted till now
        self._producers = ThreadSafeProducerSet()
        self._consumers = ThreadSafeConsumerDict()
        self._lock = threading.Lock()

    def get_length(self) -> int:
        """Return the length of the topic."""
        # return len(self._logs) # deprecated
        # note that this might not be same as self._len because the slave might
        # be running behind the master
        return execute_read_query(
            f"""
            SELECT COUNT(*) 
            FROM log WHERE topic_name = '{self._name}' 
            AND partition_index = '{self._partition_index}'
            """
        ).scalar()

    def get_log(self, index: int) -> str:
        """Return the log at the given index."""
        # return self._logs[index] # deprecated
        return execute_read_query(
            f"""
            SELECT *
            FROM log WHERE topic_name = '{self._name}'
            AND partition_index = '{self._partition_index}'
            AND id = '{index}'
            """
        ).fetchone()['message']

    # deprecated - no longer storing logs in memory
    # def add_log(self, log: Log) -> int:
    #     """Add a log to the topic and return its index."""
    #     return self._logs.append(log)

    def increment_length(self) -> int:
        """Increment the length of the and return old length."""
        with self._lock:
            old_len = self._len
            self._len += 1
        return old_len


    def add_producer(self, producer_id: str) -> None:
        """Add a producer to the topic."""
        self._producers.add(producer_id)

    def add_consumer(self, consumer_id: str, partition_index: int, offset: int = 0) -> None:
        """Add a consumer to the topic with given offset."""
        self._consumers.add(consumer_id, partition_index, offset)

    def check_producer(self, producer_id: str) -> bool:
        """Return whether the producer is in the topic."""
        return self._producers.contains(producer_id)

    def check_consumer(self, consumer_id: str, partition_index: int) -> bool:
        """Return whether the consumer is in the topic."""
        return self._consumers.contains(consumer_id, partition_index)

    def get_consumer_offset(self, consumer_id: str, partition_index: int) -> int:
        """Return the consumer offset."""
        return self._consumers.get_offset(consumer_id, partition_index)

    def get_and_increment_consumer_offset(
        self, consumer_id: str, partition_index: int, threshold: int
    ) -> int:
        """Return the consumer offset and increment it by one."""
        return self._consumers.get_offset_and_increment(consumer_id, partition_index, threshold)
