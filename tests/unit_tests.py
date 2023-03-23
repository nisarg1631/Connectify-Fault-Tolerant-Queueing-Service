import requests

# Test create topic

topic_name = "test_topic_n"
topic_name2 = "test_topic_n_2"
topic_name3 = "test_topic_n_3"
topic_name4 = "test_topic_n_4"

# Test create topic

response = requests.post(
    "http://172.19.0.1:8080/topics", json={"name": topic_name}
)
assert response.status_code == 200
assert response.json()["status"] == "success"
assert (
    response.json()["message"] == f"Topic '{topic_name}' created successfully."
)

# Test create topic with number of partitions specified

response = requests.post(
    "http://172.19.0.1:8080/topics", json={"name": topic_name2, "number_of_partitions":7}
)
assert response.status_code == 200
assert response.json()["status"] == "success"
assert (
    response.json()["message"] == f"Topic '{topic_name2}' created successfully."
)

# Test creation of duplicate topic

response = requests.post(
    "http://172.19.0.1:8080/topics", json={"name": topic_name2}
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Topic already exists."

# Test get topics
response = requests.get("http://172.19.0.1:8080/topics")
assert response.status_code == 200
assert response.json()["status"] == "success"
assert response.json()["topics"] == [topic_name, topic_name2]

# Test register consumer
response = requests.post(
    "http://172.19.0.1:8080/consumer/register", json={"topic": topic_name}
)
assert response.status_code == 200
assert response.json()["status"] == "success"
consumer_id = response.json()["consumer_id"]

# Test register consumer when topic doesnt exist

response = requests.post(
    "http://172.19.0.1:8080/consumer/register", json={"topic": topic_name3}
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Topic does not exist."

# Test register producer when topic exists

response = requests.post(
    "http://172.19.0.1:8080/producer/register", json={"topic": topic_name}
)
assert response.status_code == 200
assert response.json()["status"] == "success"
producer_id = response.json()["producer_id"]

# Test register producer when topic doesnt exist

response = requests.post(
    "http://172.19.0.1:8080/producer/register", json={"topic": topic_name3}
)
assert response.status_code == 200
assert response.json()["status"] == "success"

# Test produce message
response = requests.post(
    "http://172.19.0.1:8080/producer/produce",
    json={
        "topic": topic_name,
        "producer_id": producer_id,
        "message": "test_message",
    },
)
assert response.status_code == 200
assert response.json()["status"] == "success"

# Test produce message with partition index

response = requests.post(
    "http://172.19.0.1:8080/producer/produce",
    json={
        "topic": topic_name,
        "producer_id": producer_id,
        "message": "test_message2",
        "partition_index":0
    },
)
assert response.status_code == 200
assert response.json()["status"] == "success"

# Test produce message with partition index invalid

response = requests.post(
    "http://172.19.0.1:8080/producer/produce",
    json={
        "topic": topic_name,
        "producer_id": producer_id,
        "message": "test_message2",
        "partition_index":100
    },
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Invalid Partition Number."


# Test produce message when topic does not exist

response = requests.post(
    "http://172.19.0.1:8080/producer/produce",
    json={
        "topic": topic_name4,
        "producer_id": producer_id,
        "message": "test_message",
    },
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Topic does not exist."

# Test produce message when producer not registered within topic

response = requests.post(
    "http://172.19.0.1:8080/producer/produce",
    json={
        "topic": topic_name2,
        "producer_id": producer_id,
        "message": "test_message",
    },
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Producer not registered with topic."

# Test size over all partitions of a topic
response = requests.get(
    "http://172.19.0.1:8080/size",
    json={"topic": topic_name, "consumer_id": consumer_id},
)
assert response.status_code == 200
assert response.json()["status"] == "success"
assert len(response.json()["sizes"]) == 2
total = 0
for dict in response.json()["sizes"]:
    if dict["partition_number"] == 0:
        assert dict["size"] >= 1
    total += dict["size"]
assert total == 2

# Test size when topic does not exist

response = requests.get(
    "http://172.19.0.1:8080/size",
    json={"topic": "non_existent", "consumer_id": consumer_id, "partition_index":0},
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Topic does not exist."

# Test size when consumer has not registered

response = requests.get(
    "http://172.19.0.1:8080/size",
    json={"topic": topic_name2, "consumer_id": consumer_id,"partition_index":0},
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Consumer not registered with topic."

# Test size when partition index invalid

response = requests.get(
    "http://172.19.0.1:8080/size",
    json={"topic": topic_name2, "consumer_id": consumer_id,"partition_index":100},
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Invalid partition number."

# Test consume when consumer registered to a topic

response = requests.get(
    "http://172.19.0.1:8080/consumer/consume",
    json={"topic": topic_name, "consumer_id": consumer_id},
)
assert response.status_code == 200
assert response.json()["status"] == "success"
assert response.json()["message"] == "test_message"

# Test consume when topic does not exist

response = requests.get(
    "http://172.19.0.1:8080/consumer/consume",
    json={"topic": topic_name4, "consumer_id": consumer_id},
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Topic does not exist."

# Test consume when consumer not registered to topic

response = requests.get(
    "http://172.19.0.1:8080/consumer/consume",
    json={"topic": topic_name2, "consumer_id": consumer_id},
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Consumer not registered with topic."

# Test size of a particular partition index

response = requests.get(
    "http://172.19.0.1:8080/size",
    json={"topic": topic_name, "consumer_id": consumer_id, "partition_index":0},
)
assert response.status_code == 200
assert response.json()["status"] == "success"
size_old =  response.json()["sizes"][0]["size"]

# Test consume to a specific partition index
response = requests.get(
    "http://172.19.0.1:8080/consumer/consume",
    json={"topic": topic_name, "partition_index":0, "consumer_id": consumer_id},
)
assert response.status_code == 200
assert response.json()["status"] == "success"
assert response.json()["message"] == "test_message2"

# Test consume to a specific partition index when index invalid
response = requests.get(
    "http://172.19.0.1:8080/consumer/consume",
    json={"topic": topic_name, "partition_index":100, "consumer_id": consumer_id},
)
assert response.status_code == 400
assert response.json()["status"] == "failure"
assert response.json()["message"] == "Invalid partition number."


# Test size reduction after consume

response = requests.get(
    "http://172.19.0.1:8080/size",
    json={"topic": topic_name, "consumer_id": consumer_id, "partition_index":0},
)
assert response.status_code == 200
assert response.json()["status"] == "success"
assert response.json()["sizes"][0]["size"] == size_old - 1

print("DONE")