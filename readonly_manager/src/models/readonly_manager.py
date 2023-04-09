import threading
from typing import Dict, List, Tuple, Set
from datetime import datetime
import random

from src.models import MetadataManager

class ReadonlyManager:
    """
    Readonly manager keeps track of {topic_name, partition_number} -> broker_host
    mapping. It also stores the list of topics.
    """
    def __init__(self, startup_nodes) -> None:
        self.metadata_manager = MetadataManager(startup_nodes)
    
    def get_partition_to_read_from(self, topic_name: str, consumer_id: str) -> Tuple[int,int]:
        """
        Given topic name and consumer id, find a partition from where read is possible. 
        Use round-robin policy, return corresponding partition index.
        """
        num_partitions = self.metadata_manager.get_partition_count(topic_name)
        for _ in range(num_partitions):
            partition_index = self.metadata_manager.get_next_partition(consumer_id)
            offset = self.metadata_manager.get_and_increment_consumer_offset(consumer_id, topic_name, partition_index)
            if offset is not None:
                return partition_index, offset
        raise Exception("No new messages to read on any partition")

    def get_broker_hosts(self, topic_name: str, partition_index: int) -> List[str]:
        """
        Given topic name and partition number, return the corresponding active brokers
        """
        brokers = self.metadata_manager.get_brokers_for_partition(topic_name, partition_index)
        random.shuffle(brokers)
        active_brokers = []
        for broker in brokers:
            if self.broker_is_active(broker):
                active_brokers.append(broker)
        return active_brokers

    def find_best_partition(self, topic_name: str, consumer_id: str) -> Tuple[int,str]:
        """
        Given topic name, find a broker handling that topic. Use round-robin policy
        to assign a broker. Return the corresponding broker hostname.
        """
        return self._topics[topic_name].get_and_increment_next_partition(consumer_id)

    def get_topics(self) -> List[str]:
        """Return the topic names."""
        return self.metadata_manager.get_all_topics()
    
    def has_topic(self, topic_name: str) -> bool:
        """Check if topic exists."""
        return self.metadata_manager.check_topic_exists(topic_name)

    def get_partition_count(self, topic_name: str) -> int:
        """Return the number of partitions in a given topic."""
        return self.metadata_manager.get_partition_count(topic_name)
    
    def is_registered(self, consumer_id: str, topic_name: str) -> bool:
        """Check if consumer is registered to topic"""
        return self.metadata_manager.check_consumer_registered(consumer_id, topic_name)
    
    def is_request_valid(self, topic_name: str, consumer_id: str, partition_number: int = None) -> str:
        """
        Perform sanity checks (is topic present, is partition number valid, is consumer registered to this topic).
        """
        if not self.has_topic(topic_name):
            raise Exception("Topic does not exist.")
        partition_count = self.get_partition_count(topic_name)
        if partition_number is not None and (partition_number >= partition_count or partition_number < 0):
            raise Exception("Invalid partition number.")
        if not self.is_registered(consumer_id, topic_name):
            raise Exception("Consumer not registered with topic.")
    
    def broker_is_active(self, broker_host) -> bool: 
        return self.metadata_manager.is_broker_active(broker_host)
    
    def get_and_increment_consumer_offset(self, consumer_id, topic_name, partition_index):
        return self.metadata_manager.get_and_increment_consumer_offset(consumer_id, topic_name, partition_index)
    
    def get_sizes(self, topic_name, consumer_id, partition_index = None):
        sizes = []
        indices = [partition_index] if partition_index is not None else range(self.get_partition_count(topic_name))
        for index in indices:
            partition_size = self.metadata_manager.get_partition_size(topic_name, index)
            consumer_offset = self.metadata_manager.get_consumer_offset(consumer_id, index) 
            sizes.append( 
                { 
                    "partition_number": index, 
                    "size": partition_size - consumer_offset,
                } 
            )
        return sizes
