from redis.cluster import RedisCluster

class MetadataManager:
    def __init__(self, startup_nodes, decode_responses=True, read_from_replicas=True):
        self.rc = RedisCluster(startup_nodes=startup_nodes, decode_responses=decode_responses, read_from_replicas=read_from_replicas)

        # conditional atomic update of consumer offsets
        self._condtional_atomic_increment_lua_script = """
        local offset = redis.call("HGET", KEYS[1], ARGV[1])
        if tonumber(offset) < tonumber(ARGV[2]) then
            redis.call("HINCRBY", KEYS[1], ARGV[1], 1)
            return offset
        else
            return ARGV[2]
        end
        """
        self._conditional_atomic_increment = self.rc.register_script(self._condtional_atomic_increment_lua_script)

    def add_broker(self, broker_name):
        if self.rc.hsetnx(name=f"broker:{broker_name}", key="partition_count", value=0):
            self.rc.zadd(name="active_brokers", mapping={broker_name: 0})
            return True
        return False
    
    def remove_broker(self, broker_name):
        if self.rc.delete(f"broker:{broker_name}") == 1:
            self.rc.zrem("active_brokers", broker_name)
            return True
        return False
    
    def check_broker_exists(self, broker_name):
        return self.rc.exists(f"broker:{broker_name}") == 1
    
    def is_broker_active(self, broker_name):
        return self.rc.zscore(name="active_brokers", value=broker_name) is not None
    
    def get_broker_partition_count(self, broker_name):
        return int(self.rc.hget(name=f"broker:{broker_name}", key="partition_count"))
    
    def activate_broker(self, broker_name):
        partition_count = self.get_broker_partition_count(broker_name)
        self.rc.zadd(name="active_brokers", mapping={broker_name: partition_count})
    
    def get_brokers_with_least_partitions(self, num_brokers = 3):
        return self.rc.zrange(name="active_brokers", start=0, end=num_brokers - 1)

    def increment_brokers_partition_count(self, broker_names):
        for broker_name in broker_names:
            self.rc.hincrby(name=f"broker:{broker_name}", key="partition_count", amount=1)
            self.rc.zadd(name="active_brokers", xx=True, incr=True, mapping={broker_name: 1})
  
    def deactivate_broker(self, broker_name):
        self.rc.zrem("active_brokers", broker_name)
    
    def add_consumer(self, consumer_id, topic_name):
        self.rc.hset(name=f"consumer:{consumer_id}", key="topic", value=topic_name)
        num_partitions = self.get_partition_count(topic_name)
        self.rc.hset(name=f"consumer:{consumer_id}:offset", mapping={partition_index: 0 for partition_index in range(num_partitions)})
    
    def check_consumer_registered(self, consumer_id, topic_name):
        return self.rc.hget(name=f"consumer:{consumer_id}", key="topic") == topic_name
    
    def check_and_add_topic(self, topic_name, num_partitions):
        if self.rc.hsetnx(name=f"topic:{topic_name}", key="partition_count", value=num_partitions):
            self.rc.rpush(f"topic:{topic_name}:partition_queue", *range(num_partitions))
            return True
        return False
    
    def get_next_partition(self, topic_name):
        return int(self.rc.lmove(first_list=f"topic:{topic_name}:partition_queue", second_list=f"topic:{topic_name}:partition_queue"))
    
    def get_new_raft_port(self):
        self.rc.setnx("raft_port", 5010)
        return int(self.rc.incr("raft_port"))
    
    def add_topic_brokers(self, topic_name, broker_hosts):
        partition_count = len(broker_hosts)
        raft_ports = [self.get_new_raft_port() for _ in range(partition_count)]
        for partition_index, brokers in enumerate(broker_hosts):
            self.rc.hset(name=f"topic:{topic_name}:{partition_index}:broker", mapping={replica_index: broker for replica_index, broker in enumerate(brokers)})
        self.rc.hset(name=f"topic:{topic_name}:size_pre", mapping={partition_index: 0 for partition_index in range(partition_count)})
        self.rc.hset(name=f"topic:{topic_name}:size_post", mapping={partition_index: 0 for partition_index in range(partition_count)})
        return raft_ports

    def check_topic_exists(self, topic_name):
        return self.rc.exists(f"topic:{topic_name}") == 1
    
    # def get_topic_brokers(self, topic_name):
    #     return list(self.rc.hgetall(name=f"topic:{topic_name}:broker").values())
    
    def get_partition_count(self, topic_name):
        return int(self.rc.hget(name=f"topic:{topic_name}", key="partition_count"))
    
    def get_brokers_for_partition(self, topic_name, partition_index):
        return list(self.rc.hgetall(name=f"topic:{topic_name}:{partition_index}:broker").values())
    
    def add_producer(self, producer_id, topic_name):
        self.rc.hset(name=f"producer:{producer_id}", key="topic", value=topic_name)
    
    def check_producer_registered(self, producer_id, topic_name):
        return self.rc.hget(name=f"producer:{producer_id}", key="topic") == topic_name
    
    def get_log_index(self, topic_name, partition_index):
        return self.rc.hincrby(name=f"topic:{topic_name}:size_pre", key=partition_index, amount=1) - 1
    
    def incr_partition_size(self, topic_name, partition_index):
        self.rc.hincrby(name=f"topic:{topic_name}:size_post", key=partition_index, amount=1)

    def get_partition_size(self, topic_name, partition_index):
        return int(self.rc.hget(name=f"topic:{topic_name}:size_post", key=partition_index))
    
    def get_consumer_offset(self, consumer_id, topic_name, partition_index):
        size = self.get_partition_size(topic_name, partition_index)
        # run a redis lua script which increments the offset if it is less than the size
        # and returns the old offset, if the offset is greater than or equal to the size
        # return the size without incrementing the offset
        offset = int(self._conditional_atomic_increment(keys=[f"consumer:{consumer_id}:offset"], args=[partition_index, size]))
        return offset if offset < size else None

    def drop_all(self):
        self.rc.flushall()
