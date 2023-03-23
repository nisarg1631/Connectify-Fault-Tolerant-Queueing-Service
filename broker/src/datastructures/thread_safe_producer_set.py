import threading
from typing import Set


class ThreadSafeProducerSet:
    """
    A thread-safe set class to store the producers registered with a
    certain topic.
    """

    def __init__(self) -> None:
        self._set: Set[str] = set()
        self._lock = threading.Lock()

    def add(self, producer_id: str) -> None:
        """Add a producer to the set."""
        with self._lock:
            self._set.add(producer_id)

    def contains(self, producer_id: str) -> bool:
        """Return whether the set contains the given producer."""
        with self._lock:
            return producer_id in self._set

    def __str__(self) -> str:
        """Return the string representation of the set."""
        return f"ThreadSafeProducerSet({self._set})"