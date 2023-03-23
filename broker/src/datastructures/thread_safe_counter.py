import threading


class ThreadSafeCounter:
    """
    A thread-safe counter class to keep track of the number of messages
    consumed by a consumer.
    """

    def __init__(self, offset: int = 0) -> None:
        self._value = offset
        self._lock = threading.Lock()

    def get(self) -> int:
        """Return the current value of the counter."""
        with self._lock:
            return self._value

    def get_and_increment(self, threshold: int) -> int:
        """Get the current value and increment it by 1 if it is less
        than the threshold."""
        with self._lock:
            current_value = self._value
            if self._value < threshold:
                self._value += 1
        return current_value

    def __str__(self) -> str:
        """Return the string representation of the counter."""
        return f"Counter({self._value})"