import threading
from typing import Dict, List, Any, Tuple
import uuid
import time
import requests
import os
import random

from src.models import MetadataManager

class DataManager:
    """
    Handles the meta-data checking and updates in the primary
    manager.
    """

    def __init__(self, startup_nodes):
        self.metadata_manager = MetadataManager(startup_nodes)

    def broker_is_active(self, broker_name) -> bool:
        """Return whether the broker is active."""
        return self.metadata_manager.is_broker_active(broker_name)

    def check_topic_exists(self, topic_name: str) -> bool:
        """Return whether the topic exists."""
        return self.metadata_manager.check_topic_exists(topic_name)
    
    def add_topic_and_return(self, topic_name: str, num_partitions: int = 2) -> List[str]:
        if not self.metadata_manager.check_and_add_topic(topic_name, num_partitions):
            raise Exception("Topic already exists.")
        broker_hosts = []
        for i in range(num_partitions): 
            min_partition_brokers = self.metadata_manager.get_brokers_with_least_partitions()
            self.metadata_manager.increment_brokers_partition_count(min_partition_brokers)
            broker_hosts.append(min_partition_brokers)
        raft_ports = self.metadata_manager.add_topic_brokers(topic_name, broker_hosts)
        return broker_hosts, raft_ports
        
    def add_producer(self, topic_name: str) -> List[str]:
        """Add a producer to the topic and return its id and #partitions"""
        producer_id = str(uuid.uuid4().hex)
        self.metadata_manager.add_producer(producer_id, topic_name)

        return [producer_id, self.metadata_manager.get_partition_count(topic_name)]
    
    def add_consumer(self, topic_name: str) -> List[str]:
        """Add a consumer to the topic and return its id and #partitions"""
        if not self.check_topic_exists(topic_name):
            raise Exception("Topic does not exist.")
        consumer_id = str(uuid.uuid4().hex)
        self.metadata_manager.add_consumer(consumer_id, topic_name)
        return [consumer_id, self.metadata_manager.get_partition_count(topic_name)]
    
    def get_broker_host(self, topic_name: str, producer_id: str, partition_index : int = None) -> Tuple[str,int]:
        """Add a log to the topic if producer is registered with topic."""
        if not self.check_topic_exists(topic_name):
            raise Exception("Topic does not exist.")
        if not self.metadata_manager.check_producer_registered(producer_id, topic_name):
            raise Exception("Producer not registered with topic.")
        
        partition_count = self.metadata_manager.get_partition_count(topic_name)
        if partition_index is None:
            partition_index = self.metadata_manager.get_next_partition(topic_name)
        else:
            if partition_count <= partition_index or partition_index < 0:
                raise Exception("Invalid Partition Number.")
        brokers = self.metadata_manager.get_brokers_for_partition(topic_name, partition_index)
        random.shuffle(brokers)
        for broker in brokers:
            if self.broker_is_active(broker):
                return broker, partition_index
        raise Exception("No active brokers for partition.")
    
    def get_log_index(self, topic_name: str, partition_index : int) -> int:
        return self.metadata_manager.get_log_index(topic_name, partition_index)
    
    def incr_partition_size(self, topic_name: str, partition_index : int) -> None:
        self.metadata_manager.incr_partition_size(topic_name, partition_index)
    
    def add_broker(self, broker_host) -> None:
        if not self.metadata_manager.add_broker(broker_host):
            raise Exception("Broker with hostname already exists.")
    
    def remove_broker(self, broker_host) -> None: 
        if not self.metadata_manager.remove_broker(broker_host):
            raise Exception("Broker with hostname not present.")
    
    def activate_broker(self, broker_host) -> None: 
        if not self.metadata_manager.check_broker_exists(broker_host):
            raise Exception("Broker with hostname does not exist.")
        if self.metadata_manager.is_broker_active(broker_host):
            raise Exception("Broker with hostname already active.")
        self.metadata_manager.activate_broker(broker_host)

    def deactivate_broker(self, broker_host) -> None: 
        if not self.metadata_manager.check_broker_exists(broker_host):
            raise Exception("Broker with hostname does not exist.")
        if not self.metadata_manager.is_broker_active(broker_host):
            raise Exception("Broker with hostname already inactive.")
        self.metadata_manager.deactivate_broker(broker_host)

    def drop_all_metadata(self) -> None:
        self.metadata_manager.drop_all()
