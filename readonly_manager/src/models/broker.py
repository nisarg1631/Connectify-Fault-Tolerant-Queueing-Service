class Broker:
    """
    Class representing a broker.
    """
    
    def __init__(self, broker):
        """Initialize a broker"""
        self._round_robin_turn = 0

        if isinstance(broker, str):
            """Initialize a broker if given a broker hostname"""
            # Add error handling (error in format of broker)
            self._broker_host = broker
            self._broker_number = int(broker.split("-")[1])
        
        elif isinstance(broker, int):
            """Initialize a broker if given a broker number"""
            # Add error handling (broker <= 0)
            self._broker_host = "broker-" + str(broker)
            self._broker_number = broker

    def get_name(self) -> str:
        """Return the host name of the broker."""
        return self._broker_host
    
    def get_number(self) -> int:
        """Return the broker number."""
        return self._broker_number
    
    def get_last_requested(self) -> int:
        """Return last request turn number"""
        return self._round_robin_turn

    def set_last_requested(self, turn_number: int) -> None:
        """Return last request turn number"""
        self._round_robin_turn = turn_number