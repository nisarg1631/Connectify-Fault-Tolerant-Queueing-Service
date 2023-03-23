""""
TESTS FOR CHECKING CONCURRENT EXECUTION OF CONSUMER SPECIFIC FUNCTIONS
"""
import requests
import random
import time

TIMES = 100
counters = [[0 for _ in range(10)] for _ in range(10)]
id = 5

def cons(i):

    for time in range(TIMES):

        # create topic
        response = requests.post(
            "http://172.19.0.1:8080/topics",
            json={"name": f"test_topic_{id}_{time}", "number_of_partitions":9},
        )
        print(response.json()["message"])
        
        #register to a topic
        response = requests.post(
            "http://172.19.0.1:8080/consumer/register",
        json={"topic": f"test_topic_{id}_{time}"},
        )
        assert response.status_code == 200
        consumer_id = response.json()["consumer_id"]
        list1 = [0,1,2,3,4]
        
        # get list of topics
        response = requests.get("http://172.19.0.1:8080/topics")

        assert response.status_code == 200
        print(response.json()["topics"])
    print(f"Consumer {i} done")


import threading

threads = []
for i in range(10):
    threads.append(threading.Thread(target=cons, args=(i,)))
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()