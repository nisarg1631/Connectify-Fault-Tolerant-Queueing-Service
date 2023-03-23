""""
TESTS FOR CHECKING CONCURRENT EXECUTION OF PRODUCERS AND CONSUMERS
"""

import requests
import random
import time

P_MESSAGES = 19
C_MESSAGES = 200
counters = [[0 for _ in range(10)] for _ in range(10)]
id = 5
def prod(i):
    
    # create topic
    response = requests.post(
        "http://172.19.0.1:8080/topics", json={"name": f"test_topic_r{id}","number_of_partitions":5}
    )
    if response.status_code != 200:
        print(response.json()["message"])
    else : 
        print(f"producer {i} created topic")
    
    # register to topic
    response = requests.post(
        "http://172.19.0.1:8080/producer/register",
        json={"topic": f"test_topic_r{id}"},
    )
    assert response.status_code == 200
    producer_id = response.json()["producer_id"]
    list1 = [0,1,2,3,4]

    # produce to topic
    for cnt in range(P_MESSAGES):
        part_id = random.choice(list1)
        response = requests.post(
            "http://172.19.0.1:8080/producer/produce",
            json={
                "producer_id": producer_id,
                "topic": f"test_topic_r{id}",
                "message": f"{i} {cnt}",
            },
        )
        print(f"produced at {part_id}")

        if response.status_code != 200 : 
            print(response.json()["message"])
        assert response.status_code == 200
    print(f"Producer {i} done")

def cons(i):

    # register to topic
    time.sleep(5)
    response = requests.post(
        "http://172.19.0.1:8080/consumer/register",
        json={"topic": f"test_topic_r{id}"},
    )
    assert response.status_code == 200
    consumer_id = response.json()["consumer_id"]
    list1 = [0,1,2,3,4]

    # consume from the registered topic
    for cnt in range(C_MESSAGES):
        part_id = random.choice(list1)
        response = requests.get(
            "http://172.19.0.1:8080/size",
            json={
                "consumer_id": f"{consumer_id}",
                "topic": f"test_topic_r{id}",
            }
        )
        assert response.status_code == 200
        total = 0
        for dict in response.json()["sizes"]:
            total += dict["size"]
        if total >= 1:
            response = requests.get(
                "http://172.19.0.1:8080/consumer/consume",
                json={
                    "consumer_id": f"{consumer_id}",
                    "topic": f"test_topic_r{id}",
                    "message": f"{i} {cnt}",
                },
            )
            assert response.status_code == 200
            msg = response.json()["message"]
            print(msg)
    print(f"Consumer {i} done")


import threading

threads = []
for i in range(10):
    threads.append(threading.Thread(target=prod, args=(i,)))
    threads.append(threading.Thread(target=cons, args=(i,)))
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
