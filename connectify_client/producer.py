import requests
import aiohttp
from urllib.parse import urljoin
from typing import Dict, Tuple, List

from .routes import Routes
from .async_requests import AsyncRequests


class Producer:
    """
    Producer class to interact with the queue.

    address: str - the address of the broker
    port: int - the port of the broker
    protocol: str - the protocol to use (currently only http is supported)
    """

    def __init__(
        self, address: str, port: int, protocol: str = "http"
    ) -> None:
        self.broker = protocol + "://" + address + ":" + str(port)
        self.topics: Dict[str, str] = {}
        self.async_requestor = AsyncRequests()

    async def _register(
        self, session: aiohttp.client.ClientSession, topic_name: str
    ) -> Tuple[bool, str]:
        """
        Register a topic to produce to if not already registered.
        """
        if topic_name not in self.topics:
            try:
                url = urljoin(self.broker, Routes.register_producer)
                json_data: Dict[str, str] = {"topic": topic_name}
                async with session.post(url, json=json_data) as response:
                    response_status = response.status
                    response_json = await response.json()
                    if response_status == 200:
                        producer_id = response_json["producer_id"]
                        self.topics[topic_name] = producer_id
                        return True, "Topic registered."
                    elif response_status == 400:
                        return False, response_json["message"]
                    else:
                        return False, await response.text()
            except Exception as e:
                return False, str(e)
        return False, "Topic already registered."

    async def _produce(
        self,
        session: aiohttp.client.ClientSession,
        message: str,
        topic_name: str,
        partition_index: int = None
    ) -> Tuple[bool, str]:
        """
        Produce a message to a given partition of a topic. If no partition 
        is provided, partition will be chosen in a round-robin manner.
        """
        if topic_name in self.topics:
            try:
                url = urljoin(self.broker, Routes.produce_message)
                json_data: Dict[str, str] = {
                    "topic": topic_name,
                    "producer_id": self.topics[topic_name],
                    "message": message,
                }
                if partition_index is not None:
                    json_data["partition_index"] = partition_index
                async with session.post(url, json=json_data) as response:
                    response_status = response.status
                    response_json = await response.json()
                    if response_status == 200:
                        return True, "Message produced."
                    elif response_status == 400:
                        return False, response_json["message"]
                    else:
                        return False, await response.text()
            except Exception as e:
                return False, str(e)
        return False, "Topic not registered."

    def register(self, topic_name: str) -> Tuple[bool, str]:
        """
        Register a topic to produce to.

        Params:
            topic_name - the name of the topic to register
        
        Returns:
            A tuple of (success, message)
        """
        return self.async_requestor.run(
            self._register, [{"topic_name": topic_name}]
        )[0]

    def produce_across_topics(
        self, message: str, topics: List[str]
    ) -> List[Tuple[bool, str]]:
        """
        Produce a message to multiple topics. 

        Params:
            topics - the list of topics to produce to
            message - the message to produce
        
        Returns:
            A list of tuples of (success, message)
            There is a one-to-one correspondence between the topics parameter
            and the returned list. One tuple per topic indicating whether the 
            message was produced successfully in that topic.
        """
        return self.async_requestor.run(
            self._produce,
            [
                {"message": message, "topic_name": topic_name}
                for topic_name in topics
            ]
        )
    
    def produce_across_partitions_of_topic(
        self, message: str, topic_name: str, partition_indices: List[str]
    ) -> List[Tuple[bool,str]]:
        """
        Produce a message to multiple partitions of a given topic. 

        Params:
            topic_name - the name of the topic to produce to
            partition_indices - the list of partitions to produce to
            message - the message to produce
        
        Returns:
            A list of tuples of (success, message)
            There is a one-to-one correspondence between the `partition_indices` parameter
            and the returned list. One tuple per partition_index indicating whether the 
            message was produced successfully in that partition.
        """
        return self.async_requestor.run(
            self._produce,
            [
                {"message": message, "topic_name": topic_name, "partition_index": partition_index}
                for partition_index in partition_indices
            ]
        )

    def produce(self, message: str, topic_name: str) -> Tuple[bool, str]:
        """
        Produce a message to a topic.

        Params:
            topic_name - the name of the topic to produce to
            message - the message to produce

        Returns:
            A tuple of (success, message)
        """
        return self.produce_across_topics(message, [topic_name])[0]
    
    def produce_to_partition(self, message: str, topic_name: str, partition_index: int) -> Tuple[bool,str]:
        """
        Produce a message to a given partition of a topic.

        Params:
            message - the message to produce
            topic_name - the name of the topic to produce to
            partition_index - the partition to be produced to

        Returns:
            A tuple of (success, message)
        """
        return self.produce_across_partitions_of_topic(message, topic_name, [partition_index])[0]

    def produce_multiple_messages(
        self,  messages: List[str], topic_name: str
    ) -> List[Tuple[bool, str]]:
        """
        Produce multiple messages to a topic. 

        Params:
            topic_name - the name of the topic to produce to
            messages - the list of messages to produce
        
        Returns:
            A list of tuples of (success, message)
        
        Note: Does not guarantee order.
        """
        return self.async_requestor.run(
            self._produce,
            [
                {"message": message, "topic_name": topic_name}
                for message in messages
            ]
        )
    
    def produce_multiple_messages_to_partition(
        self, messages: List[str], topic_name: str, partition_index: int
    ) -> List[Tuple[bool, str]]:
        """
        Produce multiple messages to a topic. 

        Params:
            messages - the list of messages to produce
            topic_name - the name of the topic to produce to
            partition_index - the partition to produce to
        
        Returns:
            A list of tuples of (success, message)
        
        Note: Does not guarantee order.
        """
        return self.async_requestor.run(
            self._produce,
            [
                {"message": message, "topic_name": topic_name, "partition_index": partition_index}
                for message in messages
            ]
        )

    def close(self) -> None:
        """
        Close the producer.
        """
        self.async_requestor.close()