

import requests
from connectify_client import Consumer, Producer

MESSAGES = 300

response = requests.post(
    "http://172.19.0.1:8080/topics", json={"name": "test_topic"}
)

consumer = Consumer("172.19.0.1", 8080)
consumer.register("test_topic")

cnt = 0

while True:
    status, message = consumer.consume("test_topic")
    if status:
        cnt += 1
    if cnt == MESSAGES:
        break

print("Cons Done")
consumer.close()