## Connectify-Client : Client Side Libary

This is the client side library for our multi-broker distributed queue service **connectify**. Our client side library is written in Python and is called `connectify_client`. The following is a detailed documentation of its interface.

#### Consumer

- `register()`: Register a topic to consume from.
    - Params:
        - `topic_name` - the name of the topic to register
    - Returns:
        - Tuple of (`success`, `message`).

- `consume()`: Consume a message from any partition of a topic. Partition is chosen arbitrarily.
    - Params:
        - `topic_name` - the name of the topic to consume from
    - Returns:
        - Tuple of (`success`, `message`).
        - If `success` is True:
            - `message` is the message retrieved from the given topic
        - Otherwise, it is an error message.

- `consume_multiple()`: Consume multiple messages from a topic. Different messages may be read from different partitions.
    - Params:
        - `n` - the number of messages to consume
        - `topic_name` - the name of the topic to consume from
    - Returns:
        - A list of tuples of (`success`, `message`).
        - If `success` is True:
            `message` is the message retrieved from the given topic
        - Otherwise, it is an error message.

- `consume_from_partition()`: Consume a message from a given partition of a topic.
    - Params:
        - `topic_name` - the name of the topic to consume from
        - `partition_index` - the partition of the topic to consume from
    - Returns:
        - Tuple of (`success`, `message`).
        - If `success` is True:
            - `message` is the message retrieved from the given partition
        - Otherwise, it is an error message.

- `consume_multiple_from_partition()`: Consume multiple messages from a given partition of a topic. 
    - Params:
        - `n` - the number of messages to consume
        - `topic_name` - the name of the topic to consume from
        - `partition_index` - the partition of the topic to consume from
    - Returns:
        - A list of tuples of (`success`, `message`).
        - If `success` is True:
            - `message` is the message retrieved from topic
        - Otherwise, it is an error message.

- `get_queue_length()`: Get the length of all the queues (partitions) of a topic. 
    - Params:
        - `topic_name` - the name of the topic to get the length of
    - Returns:
        - Tuple of (`success`, list of `{"partition_index": x, "size": y}`).
        - If `success` is True:
            - A list of dictionaries containing the "partition_index" and "size".
        - Otherwise, it is an error message.
    
- `get_queue_length_for_partition()`: Get the length of a given queue (partition) of a topic.
    - Params:
        - `topic_name` - the name of the topic to get the length of
        - `partition_index` - the partition of the topic to get the length of
    - Returns:
        - Tuple of (`success`, `{"partition_index": x, "size": y}`).
        - If `success` is True:
            - A list of dictionaries containing the "partition_index" and "size".
        - Otherwise, it is an error message.

- `can_consume()`: Check if a topic can be consumed from.
        - Params:
            - `topic_name` - the name of the topic to check
        - Returns:
            - True if there is at least one unconsumed message in the queue.

#### Producer

- `register()`: Register a topic to produce to.
    - Params:
        - `topic_name` - the name of the topic to register
    - Returns:
        - Tuple of (`success`, `message`).

- `produce()`: Produce a message to a topic.
    - Params:
        - `message` - the message to produce
        - `topic_name` - the name of the topic to produce to
    - Returns:
       - A tuple of (`success`, `message`)

- `produce_multiple_messages()`: Produce multiple messages to a topic. 
    - Params:
        - `messages` - the list of messages to produce
        - `topic_name` - the name of the topic to produce to
    - Returns:
        - A list of tuples of (`success`, `message`)

- `produce_to_partition()`: Produce a message to a given partition of a topic.
    - Params:
        - `message` - the message to produce
        - `topic_name` - the name of the topic to produce to
        - `partition_index` - the partition to be produced to
    - Returns:
       - A tuple of (`success`, `message`)

- `produce_multiple_to_partition()`: Produce multiple messages to a given partition of a topic.
    - Params:
        - `messages` - the list of messages to produce
        - `topic_name` - the name of the topic to produce to
        - `partition_index` - the partition to be produced to
    - Returns:
        - A list of tuples of (`success`, `message`)

- `produce_across_topics()`: Produce a message to multiple topics.
    - Params:
        - `message` - the message to produce
        - `topics` - the list of topics to produce to
    - Returns:
        - A list of tuples of (`success`, `message`)
        - There is a one-to-one correspondence between the topics parameter and the returned list. One tuple per topic indicating whether the message was produced successfully in that topic.

- `produce_across_partitions_of_topic()`: Produce a message to multiple partitions of a given topic.
    - Params:
        - `message` - the message to produce
        - `topics` - the list of topics to produce to
        - `partition_indices` - the list of partitions to produce to
    - Returns:
        - A list of tuples of (`success`, `message`)
        - There is a one-to-one correspondence between the topics parameter and the returned list. One tuple per topic indicating whether the message was produced successfully in that topic.  

> We use an async requests module in order to make multiple consume/produce requests faster. To make use of this call `produce_multiple()`/`consume_multiple()` or the `from_partition` versions. However, of course, this means that you **may not be producing/consuming to/from the queue in-order**. To guarantee order while making multiple produce/consume requests use the `produce()`/`consume()` calls or their `from_partition` versions (as needed).