import threading
from typing import Set


class ThreadSafeConsumerSet:
    """
    A thread-safe set class to store the producers registered with a
    certain topic.
    """

    def __init__(self) -> None:
        self._set: Set[str] = set()
        self._lock = threading.Lock()

    def add(self, consumer_id: str) -> None:
        """Add a consumer to the set."""
        with self._lock:
            self._set.add(consumer_id)

    def contains(self, consumer_id: str) -> bool:
        """Return whether the set contains the given producer."""
        with self._lock:
            return consumer_id in self._set

    def __str__(self) -> str:
        """Return the string representation of the set."""
        return f"ThreadSafeConsumerSet({self._set})"