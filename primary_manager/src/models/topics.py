import threading
from typing import List, Tuple

from src.datastructures import (
    ThreadSafeDict,
    ThreadSafeConsumerSet
)


class Topic:
    """
    A topic is a collection of log messages that are related to each other.
    """

    def __init__(self, name: str, partitions: int):
        self._name = name
        self._producers = ThreadSafeDict()
        self._consumers = ThreadSafeConsumerSet()
        self._partitions = partitions
        self._broker_list = []


    def add_producer(self, producer_id: str) -> None:
        """Add a producer to the topic."""
        self._producers.add(producer_id)
    
    def add_consumer(self, consumer_id: str) -> None:
        """Add a consumer to the topic"""
        self._consumers.add(consumer_id)

    def check_producer(self, producer_id: str) -> bool:
        """Return whether the producer is in the topic."""
        return self._producers.contains(producer_id)

    def check_consumer(self, consumer_id :str) -> bool:
        """Return whether the consumer is in the topic"""
        return self._consumers.contains(consumer_id)
    
    def update_partition_index(self, producer_id: str, partition_index: int ) -> str :
        """Update the last partition index contacted by this producer"""
        self._producers.update(producer_id, partition_index, self._partitions)
        return (self._broker_list[partition_index], partition_index)
       
    def round_robin_return_and_update_partition_index(self, producer_id: str) -> Tuple[str,int] :
        """Update the last partition index contacted by this producer in round robin manner"""
        partition_index =  self._producers.return_and_update(producer_id,self._partitions)
        return (self._broker_list[partition_index], partition_index)

    def append_broker(self, broker_host:str) -> None:
        """Append broker host name to list of brokers"""
        self._broker_list.append(broker_host)

    def get_partition_count(self) -> int:
        return self._partitions
    
    def get_broker_list(self) -> List[str]:
        return self._broker_list

