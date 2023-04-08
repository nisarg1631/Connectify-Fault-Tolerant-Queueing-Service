#!/bin/bash

curl --header "Content-Type: application/json" --request POST -d '{"name":"t1", "partition_index":0, "other_brokers":["broker-2","broker-3"], "port":"5050"}' http://172.24.0.18:5000/topics
curl --header "Content-Type: application/json" --request POST -d '{"name":"t1", "partition_index":0, "other_brokers":["broker-1","broker-3"], "port":"5050"}' http://172.24.0.19:5000/topics
curl --header "Content-Type: application/json" --request POST -d '{"name":"t1", "partition_index":0, "other_brokers":["broker-1","broker-2"], "port":"5050"}' http://172.24.0.20:5000/topics


curl --header "Content-Type: application/json" --request POST -d '{"name":"t2", "partition_index":0, "other_brokers":["broker-2","broker-3"], "port":"5051"}' http://172.24.0.18:5000/topics
curl --header "Content-Type: application/json" --request POST -d '{"name":"t2", "partition_index":0, "other_brokers":["broker-1","broker-3"], "port":"5051"}' http://172.24.0.19:5000/topics
curl --header "Content-Type: application/json" --request POST -d '{"name":"t2", "partition_index":0, "other_brokers":["broker-1","broker-2"], "port":"5051"}' http://172.24.0.20:5000/topics

# curl --header "Content-Type: application/json" --request POST -d '{"topic":"t1", "producer_id":"442d037bbae846519f227d778209ff93", "message":"l1", "partition_index":0, "log_index":0}' 172.24.0.20:5000/producer/produce