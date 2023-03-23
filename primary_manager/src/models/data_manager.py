import threading
from typing import Dict, List, Any, Tuple
import uuid
import time
import requests
import os

from src.models import Topic
from src import db, app
from src import TopicDB, BrokerDB, ProducerDB, PartitionDB, ConsumerDB, RequestLogDB
from src import sync_broker_metadata

class DataManager:
    """
    Handles the meta-data checking and updates in the primary
    manager.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._topics: Dict[str, Topic] = {}
        self._active_brokers: Dict[str, int] = {}
        self._inactive_brokers : Dict[str,int] = {}
        # broker health - 0 means healthy, for every failue
        # increment by 1, when counter reaches -3, mark broker
        # as inactive
        self._broker_health : Dict[str, int] = {}


    def init_from_db(self) -> None:
        """Initialize the manager from the db."""
        topics = TopicDB.query.all()
        for topic in topics:
            self._topics[topic.name] = Topic(topic.name, topic.partitions)
            # get producers with topic_name=topic.name
            producers = ProducerDB.query.filter_by(topic_name=topic.name).all()
            for producer in producers:
                self._topics[topic.name].add_producer(producer.id)
            consumers = ConsumerDB.query.filter_by(topic_name=topic.name).all()
            for consumer in consumers:
                self._topics[topic.name].add_consumer(consumer.id)
    
        brokers = BrokerDB.query.all()
        for broker in brokers:
            self._broker_health[broker.name] = 0
            if broker.status == 1:
                self._active_brokers[broker.name] = 0
            else :
                self._inactive_brokers[broker.name] = 0
            
        partitions = PartitionDB.query.order_by(PartitionDB.ind).all()
        for partition in partitions:
            self._topics[partition.topic_name].append_broker(partition.broker_host)
            if partition.broker_host in self._active_brokers:
                self._active_brokers[partition.broker_host]+=1
            else :
                self._inactive_brokers[partition.broker_host]+=1
    
    def get_brokers(self) -> List[str]:
        """Return the complete list of brokers."""
        with self._lock:
            return list(self._broker_health.keys())
        
    
    def reset_broker_health(self, broker_name) -> int:
        """Reset broker health to 0 and return old health"""
        with self._lock:
            old_health = self._broker_health[broker_name]
            self._broker_health[broker_name] = 0
        return old_health
                
    
    def decrement_broker_health(self, broker_name) -> int:
        """Decrement broker health by 1 and return old health"""
        with self._lock:
            old_health = self._broker_health[broker_name]
            if old_health != -3:
                self._broker_health[broker_name] -= 1
        return old_health

    
    def broker_is_active(self, broker_name) -> bool:
        """Return whether the broker is active."""
        with self._lock:
            return broker_name in self._active_brokers
        
    def queue_request(self, broker_name: str, endpoint: str, json_data: Dict[str, Any]) -> None:
        """Queue the request in the db."""
        db.session.add(RequestLogDB(broker_name=broker_name, endpoint=endpoint, json_data=json_data))
        db.session.commit()

    def play_requests(self, broker_name: str) -> None:
        """Play the requests in the db and delete them from database."""
        app.logger.info(f"Playing requests for broker: {broker_name}")
        pending_requests = RequestLogDB.query.filter_by(broker_name=broker_name).order_by(RequestLogDB.id).all()
        for request in pending_requests:
            requests.post(request.endpoint, json=request.json_data)
            db.session.delete(request)
        db.session.commit()

    def _contains(self, topic_name: str) -> bool:
        """Return whether the master queue contains the given topic."""
        with self._lock:
            return topic_name in self._topics
    
    def add_topic_and_return(self, topic_name: str, num_partitions: int = 2) -> List[str]:
        broker_hosts = []
        # choosing [broker] with minimum number of partitions
        with self._lock:
            if topic_name in self._topics:
                raise Exception("Topic already exists.")
            self._topics[topic_name] = Topic(topic_name, num_partitions)
            for i in range(num_partitions) : 
                min_partition_broker = min(self._active_brokers, key=self._active_brokers.get)
                self._active_brokers[min_partition_broker]+=1
                broker_hosts.append(min_partition_broker)
                self._topics[topic_name].append_broker(broker_hosts[i])
            db.session.add(TopicDB(name=topic_name, partitions = num_partitions))
            db.session.commit()
            for index in range(num_partitions) : 
                db.session.add(PartitionDB(ind=index,topic_name = topic_name, broker_host = broker_hosts[index]))
                db.session.commit()
        return broker_hosts
        
    def add_producer(self, topic_name: str) -> List[str]:
        """Add a producer to the topic and return its id and #partitions"""
        producer_id = str(uuid.uuid4().hex)
        self._topics[topic_name].add_producer(producer_id)

        # add to db
        db.session.add(ProducerDB(id=producer_id, topic_name=topic_name))
        db.session.commit()

        return [producer_id, self._topics[topic_name].get_partition_count()]
    
    def add_consumer(self, topic_name: str) -> List[str]:
        """Add a consumer to the topic and return its id and #partitions"""
        if not self._contains(topic_name):
            raise Exception("Topic does not exist.")
        consumer_id = str(uuid.uuid4().hex)
        self._topics[topic_name].add_consumer(consumer_id)

        # add to db
        db.session.add(ConsumerDB(id=consumer_id, topic_name=topic_name))
        db.session.commit()

        return [consumer_id, self._topics[topic_name].get_partition_count()]
    
    def get_broker_host(self, topic_name: str, producer_id: str, partition_number : int = None) -> Tuple[str,int]:
        """Add a log to the topic if producer is registered with topic."""
        if not self._contains(topic_name):
            raise Exception("Topic does not exist.")
        if not self._topics[topic_name].check_producer(producer_id):
            raise Exception("Producer not registered with topic.")
        
        broker_index = partition_number
        if partition_number is None:
            retries = self._topics[topic_name].get_partition_count()
            while retries > 0:
                broker_host, partition_index = self._topics[topic_name].round_robin_return_and_update_partition_index(producer_id)
                if self.broker_is_active(broker_host):
                    return broker_host, partition_index
                retries -= 1
            raise Exception("All brokers are inactive.")
        else:
            if self._topics[topic_name].get_partition_count() <= partition_number :
                raise Exception("Invalid Partition Number.")
            broker_host, partition_index = self._topics[topic_name].update_partition_index(producer_id, partition_number)
            if self.broker_is_active(broker_host):
                return broker_host, partition_index
            else:
                raise Exception("Broker is inactive.")
    
    def get_broker_list_for_topic(self, topic_name:str) -> List[str]:
        return self._topics[topic_name].get_broker_list()
    
    def add_broker(self, broker_host) -> None: 
        with self._lock:
            if ( broker_host in self._active_brokers ) or ( broker_host in self._inactive_brokers ) : 
                raise Exception("Broker with hostname already exists.")
            self._active_brokers[broker_host] = 0
            self._broker_health[broker_host] = 0
            db.session.add(BrokerDB(name = broker_host,status = 1))
            db.session.commit()
    
    def remove_broker(self, broker_host) -> None: 
        with self._lock:
            if ( broker_host not in self._active_brokers ) and ( broker_host not in self._inactive_brokers ) : 
                raise Exception("Broker with hostname not present.")
            if broker_host in self._active_brokers :
                self._active_brokers.pop(broker_host)
            else :
                self._inactive_brokers.pop(broker_host)
            self._broker_health.pop(broker_host)
            BrokerDB.query.filter_by(name = broker_host).delete()
            db.session.commit()
    
    def activate_broker(self, broker_host) -> None: 
        with self._lock:
            if ( broker_host not in self._inactive_brokers ): 
                raise Exception("Broker with hostname not inactive.")
            
            try:
                self.play_requests(broker_host)
            except Exception as e:
                raise Exception(f"Unable to play requests for broker {broker_host} : {e}")

            # activate on read only managers
            # read_only_count = int(os.environ["READ_REPLICAS"])
            # project_name = os.environ["COMPOSE_PROJECT_NAME"]
            # for i in range(read_only_count): #async
            #     requests.post(f"http://{project_name}-readonly_manager-{i+1}:5000/sync/broker/activate", json = {
            #         "broker_host":broker_host,
            #     })
            sync_broker_metadata("/sync/broker/activate", {
                "broker_host":broker_host,
            })
            # activate on write manager
            self._active_brokers[broker_host] = self._inactive_brokers[broker_host]
            self._inactive_brokers.pop(broker_host)
            broker = BrokerDB.query.filter_by(name = broker_host).first()
            broker.status = 1
            db.session.commit()

    def deactivate_broker(self, broker_host) -> None: 
        with self._lock:
            if ( broker_host not in self._active_brokers ): 
                raise Exception("Broker with hostname not active.")

            # deactivate on read only managers
            # read_only_count = int(os.environ["READ_REPLICAS"])
            # project_name = os.environ["COMPOSE_PROJECT_NAME"]
            # for i in range(read_only_count): #async
            #     requests.post(f"http://{project_name}-readonly_manager-{i+1}:5000/sync/broker/deactivate", json = {
            #         "broker_host":broker_host,
            #     })
            sync_broker_metadata(
                "/sync/broker/deactivate", 
                {
                    "broker_host":broker_host,
                }
            )
            # deactivate on write manager
            self._inactive_brokers[broker_host] = self._active_brokers[broker_host]
            self._active_brokers.pop(broker_host)
            broker = BrokerDB.query.filter_by(name = broker_host).first()
            broker.status = 0
            db.session.commit()
