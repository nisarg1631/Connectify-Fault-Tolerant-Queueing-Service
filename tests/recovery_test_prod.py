# make sure to run app with ProdConfig

import requests
from connectify_client import Consumer, Producer

MESSAGES = 300

response = requests.post(
    "http://172.19.0.1:8080/topics", json={"name": "test_topic"}
)

producer = Producer("172.19.0.1", 8080)
producer.register("test_topic")

cnt = 0

while True:
    status, message = producer.produce(f"test message {cnt}", "test_topic")
    if status:
        cnt += 1
    if cnt == MESSAGES:
        break

print("Prod Done")
producer.close()