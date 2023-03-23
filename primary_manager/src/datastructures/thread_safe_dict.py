import threading
from typing import Dict


class ThreadSafeDict:
    """
    A thread-safe set class to store the producers registered with a
    certain topic.
    """

    def __init__(self) -> None:
        self._dict: Dict[str,int] = {}
        self._lock = threading.Lock()

    def add(self, key: str) -> None:
        """Add an element to the set."""
        with self._lock:
            self._dict[key]=0

    def contains(self, key: str) -> bool:
        """Return whether the set contains the given producer."""
        with self._lock:
            return key in self._dict

    def return_and_update(self, key:str, num_partitions : int) -> int:
        with self._lock:
            current_value = self._dict[key]
            self._dict[key] = (self._dict[key]+1)%num_partitions
            return current_value

    def update(self,key : str, partition_index: int, num_partitions: int ) -> None:
        with self._lock:
            self._dict[key] = (partition_index+1)%num_partitions 
       

    def __str__(self) -> str:
        """Return the string representation of the set."""
        return f"ThreadSafeProducerSet({self._dict})"