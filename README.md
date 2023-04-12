# Connectify : DS-Assignment-2

## Setup 

### Docker Compose
In this system, each of the brokers, managers as well as the load balancer will all run inside a Docker container of their own (essentially as services).

The Docker Compose file (`compose.yaml`) describes the configuration of the containers (services). Here's a description of the various services:
- `gateway`: This is an nginx service which acts as a reverse proxy / load-balancer for read-managers and write-managers.
    - Only this service is exposed via a port (8080) of the gateway of the network.
- `primary_manager`: This is the write-manager service(s).
    - Several replicas.
    - Replicated by Docker Compose by specifying number in the compose file itself.
- `readonly_manager`: This is the read-manager service(s).
    - Several replicas.
    - Replicated by Docker Compose by specifying number in the compose file itself.
- `broker-[1..n]`: This is the broker service.
    - Several in number.
    - Added by mentioning `service` entries in the compose file (hard-coding). We choose this approach rather than Docker Compose replication as each broker uses a stores partitions in a separate database (having a different service name), so they are not exact replicas of each other.
- `redis-node-[1..n]`: Metadata redis cluster.
    - Multiple nodes, with replicas.
- `brokerdb-[1..n]`: Master database per broker for storing logs
    - Several in number. Each corresponding to a broker.

### Docker Networking
- User-defined bridge network named `internal` (named `connectify_internal` when set up) is created by Docker Compose. All the services are a part of this network.
- Services within this network can communicate with each other just by knowing each others' service names as the Docker daemon can do name resolution.
- Service names are assumed to remain constant and standard, hence we have used them as hostnames in the code to send HTTP requests amongst each other as this is a more convenient safer way than using bare IP addresses.

### How to Run
- Run the Docker Compose file to set up the Docker services.
```bash
docker compose up --build
```
- Run the following command to find out the IP address of the gateway of our network.
```bash
docker network inspect connectify_internal | grep "Gateway"
```
- Let's say the IP address is `172.19.0.1`. Use either our client-side library or `curl` to submit requests to `172.19.0.1:8080`. 

## Design
We implement a multi-broker distributed queue system which serves write and read requests from `producers` and `consumers` via a __client side library__. The queue manages `topics`, to which producers and consumers subscribe to. Upon a successful subscription, producers write logs to the queue which the registered consumers can read. All consumers have their own offset which maintains how many logs they have read from a given topic. In order to make our distributed queue scalable, each topic is broken into various `partitions`. Further for  high availability and fault tolerance each `partition` is replicated on multiple (in our case 3) `brokers`. The implementation of our design is discussed further in the following sections.

### Project Structure
The project consists of various components that interact with each other to serve a request initiated via the client side library. They are listed as follows : 

##### Write Manager/ Primary Manager 
- __Function__ : The primary manager handles all requests involving __adding new or additional data__ to the queue. Redirection of requests to the appropriate broker depending on the partition number of the topic (or in a *round robin fashion*) is also performed here. It implements a __health check protocol__ to maintain the validity of brokers as well as clients. Any functions involving adding or removing of brokers are also performed via the primary manager. 
- **Associated Databases :** It updates and reads from the Redis Cluster for keeping track of and updating the the metadata of the queue.
- **Requests Handled :** 
    - `POST` on `/topics`
    - `POST` on `/producer/register`
    - `POST` on `/consumer/register`
    - `POST` on `/producer/produce`
- **Code Structure :**
    - __src__ - the directory containing the primary application with the in-memory datastructures, models and API support
    - __models__ - implementations of `Data_Manager` and `Metadata_Manager` abstracted using classes. The `Data_Manager` contains the business logic for handling requests such as checking the validity of a request, adding a new topic, registering a producer, registering a consumer, round robin allocation of produce requests, etc. The `Metadata_Manager` is purely transactional and provides an interface for interacting with the Redis Cluster.
    - __views.py__ - the file containing the HTTP API endpoints for interacting with the primary manager.
    - __json_validator.py__ - the file containing the validator for validating the request JSON body based on the provided schema

##### Read-Ony Managers 
- **Function** : The read-only managers serve requests concerned with __reading data__ from the queue. Primatily it 
- **Associated Databases :** It updates and reads from the Redis Cluster for keeping track of and updating the the metadata of the queue.
- **Requests Handled :**
    - `GET` on `/topics`
    - `GET` on `/consumer/consume`
    - `GET` on `/size`
- **Code Structure :**
    - __src__ - the directory containing the primary application with the in-memory datastructures, models and API support
    - __models__ - implementations of `Readonly_Manager` and `Metadata_Manager` abstracted using classes. The `Readonly_Manager` contains the business logic for handling requests such as checking the validity of a request, round robin allocation of consume requests, etc. The `Metadata_Manager` is purely transactional and provides an interface for interacting with the Redis Cluster.
    - __views.py__ - the file containing the HTTP API endpoints for interacting with the read-only manager.
    - __json_validator.py__ - the file containing the validator for validating the request JSON body based on the provided schema

##### Brokers :
- **Function:** The brokers serve as the entity which interact with the queue data for writes as well as reads. Each broker handles zero to many partitions of a topic and any read/write request made to any of its partitions is forwarded to the broker after validity checks are performed at a higher level. The broker then simply performs the update or returns the data requested from it. 
- **Associated Databases :** Each broker has its corresponding Broker Database which handles all the queue data of the various partitions present in it. It does not handle requests concerning metadata updates or reads such as registering a producer or `GET`ting the list of topics.
- **Requests Handled :**
    - `GET` on `/consumer/consume`
    - `POST` on `/topics`
    - `POST` on `/producer/produce`
- **Code Structure :**
    - __src__ - the directory containing the primary application with the in-memory datastructures, models and API support
    - __models__ - implementations for various concepts of the queue such as  `Topic` and `Master_Queue`
    - __views.py__ - the file containing the HTTP API endpoints for interacting with the broker.
    - __json_validator.py__ - the file containing the validator for validating the request JSON body based on the provided schema
    - __db_models__ - the directory containing the database models for programmatically interacting with the database using `SQLAlchemy`

##### Load Balancer and Reverse Proxy 

We use `nginx` as a top level load balancer and a reverse proxy. All requests are directed to the nginx container which in turn redirects them appropriately within the docker network we have created. It serves the following purposes : 
- Redirection of appropriate requests to the singular primary manager.
- Redirection of appropriate requests to one of the multiple read-only managers in a round robin manner. 
- Act as a reverse proxy for the read only managers. Since the read-only managers are created as replicas in the docker network, their IP Addresses are dynamically created everytime they are instantiated and are not visible to us. To be able to redirect requests to these dynamically generated IP-Addresses, nginx provides a reverse proxy from the server name of the read only managers (which is fixed at every instantiation) to their IPs. 

### RAFT Consensus

We use the Python library `pysncobj` to achieve consistency among the replicated partitions managed by the different brokers through the RAFT protocol.

#### Replication of Produce Log

Our `Topic` class (which represents a partition) inherits from the `SyncObj` class, meaning each partition is a RAFT instance. Now any member method of this class can be synchronised among the brokers in order to achieve consensus by adding the decorator `@replicated_sync`. We only need to make the `add_log` (produce) method replicated, as this is the only write operation that the brokers handle.

#### Creation of a Partition

When a request to the `/topic` endpoint of the broker is made (in order to create a partition), the request data is passed into a FIFO queue for processing in a different thread. In this thread, the FIFO queue is constantly polled and when it is not empty, the request data is fetched and the instantation (creation) of a `Topic` object (and thereby `SyncObj` objects) representing a partition happens.

> This had to be done as we use Flask in threaded mode to serve our requests, meaning each POST request on the `/topic` (add topic) endpoint of the broker leads to the creation of new thread. Also, `SyncObj` upon instantiation spawns a new thread on each broker for calling several operations periodically as and when required like leader election, heartbeats, etc. If we were to instantiate our `Topic` objects in this short lived request thread then RAFT consensus through `pysyncobj` would fail as as the thread instantiated by `SyncObj` would be killed as soon as the request thread is killed after the request is served.

### Database Schemas

The various databases used and their schemas are discussed as follows. 

##### Redis Cluster
This redis cluster is used to store all the __metadata__ associated with our distributed and partitioned queue. It does not store any actual data contained in the queue. The cluster schema is as follows: 

1. Hash `broker:{broker_name}` - stores the partition count of the broker with the given name

2. List `broker_queue` - stores the names of the brokers, used as a round robin queue for health check

3. Set `active_brokers` - stores the names of the active brokers mapped to the partition count of the broker, used to quickly get 3 active brokers with the least number of partitions to allocate a new partition to

4. Hash `consumer:{consumer_id}` - stores the topic name of the consumer with the given id

5. Hash `consumer:{consumer_id}:offset` - store the mapping of the partition number to the offset of the consumer with the given id

6. List `consumer:{consumer_id}:partition_queue` - stores the partition numbers of the partitions the consumer with the given id has subscribed to, used as a round robin queue for consume requests

7. Hash `topic:{topic_name}` - stores the partition count of the topic with the given name

8. List `topic:{topic_name}:partition_queue` - stores the partition numbers of the partitions the topic with the given name has, used as a round robin queue for produce requests

9. Hash `topic:{topic_name}:{partition_index}:broker` - stores the mapping of replica number to the broker name of the partition with the given index of the topic with the given name

10. Hash `topic:{topic_name}:size` - stores the mapping of partition number to the size of the partition of the topic with the given name

11. Hash `producer:{producer_id}` - stores the topic name of the producer with the given id

##### Broker Database(s) - TODO: add RAFT related changes here
These databases store the __actual queue data__ and the associated metadata required for the handling of this data. It does not store unnecessary queue metadata. Each master database has an associated broker. The database schema is as follows: 

###### Table `topic` - contains the names and partition indices of the topics present in this portion of the queue.
- `name` - The name of the topic. 
- `partition_index` - the partition number of this topic. `name` and `partition_index` to`GET`her form a primary key which uniquely identifies a unqiue partition present within this broker.

###### Table `log` - contains the logs present in this portion of the queue
- `id` - the primary key of the table, also the unique identifier of the log along with the `topic_name`
- `topic_name` - the [foreign key](#table-topic---contains-the-names-of-the-topics-in-the-queue) to the `topic` table, the topic to which the log belongs, also the unique identifier of the log along with the `id` and  `partition_index`.
- `partition_index` -  the [foreign key](#table-topic---contains-the-names-of-the-topics-in-the-queue) to the `topic` table, the partition index of the topic to which the log belongs, also the unique identifier of the log along with the `id` ans `topic_name`
- `producer_id` - the [foreign key](#table-producer---contains-the-details-of-the-producers) to the `producer` table, the id of the producer who produced the log
- `message` - the message of the log
- `timestamp` - the timestamp of the log

###### Table `consumer` - contains the partition offsets of the consumers consuming any partition in this portion of the queue
- `id` - the primary key of the table, also the unique identifier of the consumer along with `topic_name` and `partition_index`
- `topic_name` - the [foreign key](#table-topic---contains-the-names-of-the-topics-in-the-queue) to the `topic` table, the topic to which the consumer belongs.  Also the unique identifier of the consumer along with `id` and `partition_index`
- `partition_index ` - the [foreign key](#table-topic---contains-the-names-of-the-topics-in-the-queue) to the `topic` table, the partition index of the topic to which the consumer belongs
- `offset` - the offset of the consumer for the given partition. Also the unique identifier of the consumer along with `topic_name` and `id`.

### Endpoints

The overall structure of our design looks as follows : 

##### Client Side Endpoints

These endpoints are for the calls made via our client side library.

- __GET on /topics__ : returns the list of topics. 
    - Contact a read-only manager via round robin
    - The read-only manager returns the list of topics from local memory

- __POST on /topics__ : A new topic is created
    - Contact the primary manager
    - Primary manager performs the necessary checks, returns any error found.
    - The primary database is updated with this new data
    - Information of the new topic is sent to all read-only managers 

- __POST on /producer/register__:  Producer registers to a topic
    - Contact the primary manager
    - Primary manager performs the necessary checks, returns any error found.
    - If the topic does not exist, primary manager sends a create topic request to itself
    - The primary database is updated.

- __POST on /consumer/register__:  Consumer registers to a topic
    - Contact the primary manager
    - Primary manager performs the necessary checks, returns any error found.
    - The primary database is updated
    - Information of the newly registered consumer is forwarded to all read-only manager

- __POST on /producer/produce__: Producer produces a log to a topic
    - Contact the primary manager
    - Primary manager performs the necessary checks, returns any error found.
    - If the partition index is not provided, primary manager chooses one in a   round robin fashion
    - The primary manager chooses the appropriate broker having the desired partition and forwards the request to it
    - Updates are made to the master database via the broker.
z
- __GET on /consumer/consume__:  Consumer reads a log from a topic
    - One of the read-only managers is contacted in a round robin fashion.
    - Read-only manager performs the necessary checks, returns any error found.
    - If the partition index is not provided, read-only manager chooses one in a round robin fashion.
    - The broker is contacted to `GET` the log for a chosen partition.
    - The broker contacts the slave database for the log data, and updates the offset in the master database.

    __Additional functionality__  : If a parition index is not provided, we have to choose one ourselves, however it is possible that the next partition in the round-robin does not have any logs to consume, but some other partition of the topic does have remaining logs. Hence, if a partition is chosen via round robin, the read-only manager constantly contacts partitions in brokers in a round robin fashion till it finds a partition which has some logs to consume. It then returns a log from this partition. If all logs in that topic have been consumed, an appropriate message is returned.

- __GET on /size__ when partition index is provided : Returns the number of log messages left to consume on a given partition index of a topic
    - One of the read-only managers is contacted in a round robin fashion.
    - It contacts the appropriate broker having the desired partition.
    - Broker returns the remaining logs in this partition for this consumer

- __GET on /size__ when partition index is not provided : Returns the number of log messages left to consume on a each partition of a topic
    - One of the read-only managers is contacted in a round robin fashion.
    - It contacts all the  brokers having some partition of the desired topic.
    - Each broker returns a dictionary of {partition_index : size}.
    - The read-only manager aggregates the responses of all the brokers and returns a list.

##### Administrative Endpoints

- __POST on /admin/broker/add__ : Add a new broker to the network.
    - Contact the primary manager
    - Update the primary database
    - Relay information to readonly managers for sync

- __POST on /admin/broker/remove__ : Remove a broker from the network.
    - Contact the primary manager
    - Update the primary database
    - Relay information to readonly managers for sync

- __POST on /admin/broker/activate__ : Activate an inactive broker in the network.
    - Contact the primary manager
    - Update the primary database
    - Relay information to readonly managers for sync

- __POST on /admin/broker/deactivate__ : Activate an inactive broker in the network.
    - Contact the primary manager
    - Update the primary database
    - Relay information to readonly managers for sync


### Healthcheck Service

We run a separate thread in the `primary_manager` which on a timely interval polls the registered brokers with a __GET on /__ (the root endpoint). We maintain a counter which counts down on each failure to connect with the broker. When the broker is unreachable even after 3 retries it is marked as deactivated. It no longer is used for assigning partitions to new topics. Produce and consume requests to it return failure.


### Client Side Library

See [client side library README](./connectify_client/README.md).

## Optimisations 

### Distributed Metadata
Having all the metadata related to producers, consumers and topics stored in a single database would lead to a single point of failure. Instead our design ensures high availability of data even in case of temporary database failures. To do this we use a Redis cluster with 6 nodes. Data is split into 3 groups with each group having 2 replicated nodes. Hence even if one of the nodes of a group fails, the data is still available in the other node of the group. We use the `redis-py` library to interact with the Redis cluster. Appendonly persistence is enabled in the Redis cluster. This ensures that even if the cluster is restarted, the data is not lost.

## Testing

##### Unit Testing
Test all the individual API endpoints using the `requests` library. Checked both the success paths as well as the error paths.

##### Concurrency Testing 

###### Producers and Consumers Concurrency Checks
Test the thread-safety of the in-memory datastructures using the `threading` library. Created 10 producer threads and 10 consumer threads which would be interacting with the queue simultaneously. Checked that the consumer threads are able to consume the logs in the order they were produced by the producer threads. Topic name is specified by the parameter `<id>`. Ensured ordering by logging messages of the format `<producer_id> <log_id>`. While consuming the `<log_id>` should be in increasing order for each `<producer_id>`. The number of messages to be produced can be set by the `MESSAGES` parameter in the test file. Implemented in `tests/concurrency_test.py`.

###### Producer Concurrency Checks
Test the concurrent working of various producer associated endpoints such as register producer and produce. Implemented via running 10 producer threads which are interacting with the queue simultaneously. Topic name is specified by the parameter `<id>`. Ensured ordering by logging messages of the format `<producer_id> <log_id>`. While consuming the `<log_id>` should be in increasing order for each `<producer_id>`. The number of messages to be produced can be set by the `MESSAGES` parameter in the test files . Implemented in `tests/producer_concurrency_tests.py`.

###### Consumer Concurrency Checks
Test the concurrent working of various consumer associated endpoints such as register consumer and size. Implemented via running 10 producer threads which are interacting with the queue simultaneously. Topic name is specified by the parameter `<id>`. Ensured by asserting success of the required operations.  Implemented in `tests/consumer_concurrency_tests.py`.

##### Recovery Testing
Test the recovery of the queue from a crash. Start a producer and a consumer. Kill the application. Start the application again. Check that the producer and consumer are able to interact with the queue as before. The producer should be able to produce logs and the consumer should be able to consume logs as long as the limit is not reached. Limit can be set by the `MESSAGES` parameter in the respective test files. This also tests the working of the producer and consumer in our client library as we it for creating the producer and consumer.

##### Performance Testing
We tested both the performance of the queue and the library we provide. We used asyncio to make asynchronous requests to the queue using the library. With async consume calls we saw a 50% reduction in time taken to consume the logs. Also we saw a 30-40% improvement in the time taken to process multiple requests with threading enabled in the flask application.
