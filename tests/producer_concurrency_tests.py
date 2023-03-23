""""
TESTS FOR CHECKING CONCURRENT EXECUTION OF PRODUCER SPECIFIC FUNCTIONS 
"""

import requests
import random

MESSAGES = 100
NUM_PARTITIONS = 5

counters = [[0 for _ in range(10)] for _ in range(10)]

def prod(i):
    id = 69 # vary for different topic name
    # create a topic
    response = requests.post(
        "http://172.19.0.1:8080/topics", json={"name": f"test_topic_r{id}","number_of_partitions":NUM_PARTITIONS}
    )
    if response.status_code != 200:
        print(response.json()["message"])
    else : 
        print(f"producer {i} created topic")

    # register a producer to the topic produced earlier
    response = requests.post(
        "http://172.19.0.1:8080/producer/register",
        json={"topic": f"test_topic_r{id}"},
    )
    if response.status_code != 200:
        print(response.json()["message"])
    producer_id = response.json()["producer_id"]
    list1 = list(range(NUM_PARTITIONS)) # list of partition indices

    # above producer produces MESSAGES number of messages
    for cnt in range(MESSAGES):
        part_id = random.choice(list1)
        response = requests.post(
            "http://172.19.0.1:8080/producer/produce",
            json={
                "producer_id": producer_id,
                "topic": f"test_topic_r{id}",
                "message": f"{i} {cnt}",
                "partition_number":  part_id,
            },
        )
        print(f"produced at {part_id}")

        if response.status_code != 200 : 
            print(response.json()["message"])
    print(f"Producer {i} done")

import threading

threads = []
for i in range(10):
    threads.append(threading.Thread(target=prod, args=(i,)))
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()