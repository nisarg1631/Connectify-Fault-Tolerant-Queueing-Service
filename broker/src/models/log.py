class Log:
    """
    Class representing a log message.
    """

    def __init__(self, producer_id: str, message: str, timestamp: float):
        """Initialize a log message."""
        self.producer_id = producer_id
        self.message = message
        self.timestamp = timestamp

    def __str__(self) -> str:
        """Return a string representation of the log."""
        return "Log(producer_id=%s, message=%s, timestamp=%s)" % (
            self.producer_id,
            self.message,
            self.timestamp,
        )