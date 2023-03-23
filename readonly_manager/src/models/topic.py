import random
import threading
from typing import List, Dict

class Topic:
    def __init__(self, topic_name: str, partition_count: int):
        self._lock = threading.Lock()
        self._topic_name = topic_name
        self._consumers_to_next_ptn: Dict[str,int] = {}
        self._partition_count = partition_count

    def get_topic_name(self) -> str:
        """Return the name of the topic."""
        return self._topic_name
    
    def get_consumers(self) -> List[str]:
        """Return a list of registered consumers."""
        return list(self._consumers_to_next_ptn.keys())

    def contains(self, consumer_id: str) -> bool:
        """Check if the consumer is registered."""
        return consumer_id in self._consumers_to_next_ptn.keys()

    def add_consumer(self, consumer_id: str) -> None:
        """Add a consumer to the list of registered consumers."""
        # DD: Initiliaze the next partition to be read with a random partition index.
        # This ensures that the round robin starts at different partition indices for different
        # consumers, thus balancing load across brokers
        self._consumers_to_next_ptn[consumer_id] = random.randint(0, self._partition_count-1)
    
    def get_partition_count(self) -> int:
        """Return the number of partitions in the topic."""
        return self._partition_count

    def get_and_increment_next_partition(self, consumer_id: str) -> int:
        next_partition = -1
        with self._lock:
            next_partition = self._consumers_to_next_ptn[consumer_id]
            self._consumers_to_next_ptn[consumer_id] = (self._consumers_to_next_ptn[consumer_id] + 1) % self._partition_count
        return next_partition
    
    def __str__(self) -> str:
        return "topic_name:%s, consumers_to_next_ptn:%s, partition_count:%d" %(
            self._topic_name,
            self._consumers_to_next_ptn,
            self._partition_count)

    __repr__ = __str__