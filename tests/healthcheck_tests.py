import requests


# start with 3 brokers
response = requests.post("http://172.19.0.1:8080/admin/broker/add", json={"broker_host": "broker-1", "token": "rnn1234"})
assert response.status_code == 200
response = requests.post("http://172.19.0.1:8080/admin/broker/add", json={"broker_host": "broker-2", "token": "rnn1234"})
assert response.status_code == 200
response = requests.post("http://172.19.0.1:8080/admin/broker/add", json={"broker_host": "broker-3", "token": "rnn1234"})
assert response.status_code == 200

# create topic with 3 partitions
response = requests.post(
    "http://172.19.0.1:8080/topics", json={"name": "test", "number_of_partitions":3}
)
assert response.status_code == 200
assert response.json()["status"] == "success"
assert (
    response.json()["message"] == f"Topic 'test' created successfully."
)

# produce 3 messages
response = requests.post(
    "http://172.19.0.1:8080/producer/register", json={"topic": "test"}
)
assert response.status_code == 200
assert response.json()["status"] == "success"
producer_id = response.json()["producer_id"]

response = requests.post(
    "http://172.19.0.1:8080/producer/produce",
    json={
        "topic": "test",
        "producer_id": producer_id,
        "message": "test_message1",
    },
)
assert response.status_code == 200
assert response.json()["status"] == "success"

response = requests.post(
    "http://172.19.0.1:8080/producer/produce",
    json={
        "topic": "test",
        "producer_id": producer_id,
        "message": "test_message2",
    },
)
assert response.status_code == 200
assert response.json()["status"] == "success"

response = requests.post(
    "http://172.19.0.1:8080/producer/produce",
    json={
        "topic": "test",
        "producer_id": producer_id,
        "message": "test_message3",
    },
)
assert response.status_code == 200
assert response.json()["status"] == "success"

# now kill broker-2 and run the code below

# register consumer
# response = requests.post(
#     "http://172.19.0.1:8080/consumer/register", json={"topic": "test"}
# )
# assert response.status_code == 200
# assert response.json()["status"] == "success"
# consumer_id = response.json()["consumer_id"]

# this won't be visible in the database for broker-2 as of now, but it will be visible in the database for broker-1 and broker-3
# check in the databases and verify

# produce 3 messages to specific partitions (0, 1, 2), should fail for partition 1
# response = requests.post(
#     "http://172.19.0.1:8080/producer/produce",
#     json={
#         "topic": "test",
#         "producer_id": producer_id,
#         "message": "test_message4",
#         "partition_index":0
#     },
# )
# assert response.status_code == 200
# assert response.json()["status"] == "success"

# response = requests.post(
#     "http://172.19.0.1:8080/producer/produce",
#     json={
#         "topic": "test",
#         "producer_id": producer_id,
#         "message": "test_message5",
#         "partition_index":1
#     },
# )
# assert response.status_code == 400
# print(response.json())

# response = requests.post(
#     "http://172.19.0.1:8080/producer/produce",
#     json={
#         "topic": "test",
#         "producer_id": producer_id,
#         "message": "test_message6",
#         "partition_index":2
#     },
# )
# assert response.status_code == 200
# assert response.json()["status"] == "success"

# now kill broker-1 and run the code below

# produce 2 messages, both should go to partition 2

# response = requests.post(
#     "http://172.19.0.1:8080/producer/produce",
#     json={
#         "topic": "test",
#         "producer_id": producer_id,
#         "message": "test_message7"
#     },
# )
# assert response.status_code == 200
# assert response.json()["status"] == "success"

# response = requests.post(
#     "http://172.19.0.1:8080/producer/produce",
#     json={
#         "topic": "test",
#         "producer_id": producer_id,
#         "message": "test_message8"
#     },
# )
# assert response.status_code == 200
# assert response.json()["status"] == "success"

# create topic with 2 partitions
# response = requests.post(
#     "http://172.19.0.1:8080/topics", json={"name": "test2", "number_of_partitions":2}
# )
# assert response.status_code == 200
# assert response.json()["status"] == "success"
# assert (
#     response.json()["message"] == f"Topic 'test2' created successfully."
# )

# now kill broker-3 and run the code below
# register consumer
# response = requests.post(
#     "http://172.19.0.1:8080/consumer/register", json={"topic": "test2"}
# )
# assert response.status_code == 200
# assert response.json()["status"] == "success"
# consumer_id = response.json()["consumer_id"]

# this won't be visible in the database for broker-3 as of now
# check in the databases and verify

# try to produce 2 messages, both should fail
# response = requests.post(
#     "http://172.19.0.1:8080/producer/produce",
#     json={
#         "topic": "test",
#         "producer_id": producer_id,
#         "message": "test_message9",
#     },
# )
# assert response.status_code == 400
# print(response.json())

# response = requests.post(
#     "http://172.19.0.1:8080/producer/produce",
#     json={
#         "topic": "test",
#         "producer_id": producer_id,
#         "message": "test_message10",
#     },
# )
# assert response.status_code == 400
# print(response.json())

# start all the brokers again
# the consumers should be registered to the brokers which were not up when the consumers were registered
# check in the databases and verify

# stop all brokers
# check consume and size

# response = requests.get(
#     "http://172.19.0.1:8080/consumer/consume",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37"},
# )
# assert response.status_code == 400
# print(response.json())

# response = requests.get(
#     "http://172.19.0.1:8080/consumer/consume",
#     json={"topic": "test2", "consumer_id": "db0efca9309b469ca1ca82fb2f6bff9f"},
# )
# assert response.status_code == 400
# print(response.json())

# response = requests.get(
#     "http://172.19.0.1:8080/size",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37"},
# )
# assert response.status_code == 400
# print(response.json())

# response = requests.get(
#     "http://172.19.0.1:8080/size",
#     json={"topic": "test2", "consumer_id": "db0efca9309b469ca1ca82fb2f6bff9f"},
# )
# assert response.status_code == 400
# print(response.json())

# start broker 1
# response = requests.get(
#     "http://172.19.0.1:8080/size",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37"},
# )
# print(response.json())
# assert response.status_code == 200

# response = requests.get(
#     "http://172.19.0.1:8080/consumer/consume",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37"},
# )
# print(response.json())
# assert response.status_code == 200

# response = requests.get(
#     "http://172.19.0.1:8080/size",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37"},
# )
# print(response.json())
# assert response.status_code == 200

# response = requests.get(
#     "http://172.19.0.1:8080/size",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37", "partition_index": 1},
# )
# print(response.json())
# assert response.status_code == 400

# response = requests.get(
#     "http://172.19.0.1:8080/consumer/consume",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37", "partition_index": 1},
# )
# print(response.json())
# assert response.status_code == 400

# start remaining brokers
# response = requests.get(
#     "http://172.19.0.1:8080/size",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37", "partition_index": 1},
# )
# assert response.status_code == 200
# print(response.json())

# response = requests.get(
#     "http://172.19.0.1:8080/consumer/consume",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37", "partition_index": 1},
# )
# assert response.status_code == 200
# print(response.json())

# response = requests.get(
#     "http://172.19.0.1:8080/size",
#     json={"topic": "test", "consumer_id": "9f93045c4f4e407a82d63c90c93f9c37", "partition_index": 1},
# )
# assert response.status_code == 200
# print(response.json())

# response = requests.get(
#     "http://172.19.0.1:8080/size",
#     json={"topic": "test2", "consumer_id": "db0efca9309b469ca1ca82fb2f6bff9f"},
# )
# assert response.status_code == 200
# print(response.json())

# response = requests.get(
#     "http://172.19.0.1:8080/consumer/consume",
#     json={"topic": "test2", "consumer_id": "db0efca9309b469ca1ca82fb2f6bff9f"},
# )
# assert response.status_code == 200
# print(response.json())

# response = requests.get(
#     "http://172.19.0.1:8080/size",
#     json={"topic": "test2", "consumer_id": "db0efca9309b469ca1ca82fb2f6bff9f"},
# )
# assert response.status_code == 200
# print(response.json())
