from flask import make_response, request, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError
import requests

from src import app, expects_json, data_manager

@app.errorhandler(400)
def bad_request(error):
    """Bad request handler for ill formated JSONs"""
    if isinstance(error.description, ValidationError):
        return make_response(
            jsonify(
                {"status": "failure", "message": error.description.message}
            ),
            400,
        )
    # handle other bad request errors
    return error

@app.route(rule="/topics", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {"name": {"type": "string"},"number_of_partitions":{"type":"number"}},
        "required": ["name"],
    }
)
def topics():
    """Add a topic."""

    # If method is POST add a topic
    if request.method == "POST":
        topic_name = request.get_json()["name"]
        try:
            broker_hosts = []

            if "number_of_partitions" in request.get_json():
                broker_hosts, raft_ports = data_manager.add_topic_and_return(topic_name,request.get_json()["number_of_partitions"])
            else:
                broker_hosts, raft_ports = data_manager.add_topic_and_return(topic_name)
            
            for partition_index, brokers in enumerate(broker_hosts):
                raft_port = raft_ports[partition_index]
                for replica_index, broker in enumerate(brokers):
                    other_brokers = brokers.copy()
                    other_brokers.pop(replica_index)
                    requests.post("http://"+broker+":5000/topics",json = {"name":topic_name,"partition_index":partition_index,"other_brokers":other_brokers,"port":str(raft_port)}).raise_for_status()
            return make_response(
                jsonify(
                    {
                        "status": "success",
                        "message": f"Topic '{topic_name}' created successfully.",
                    }
                ),
                200,
            )
        except Exception as e:
            return make_response(
                jsonify({"status": "failure", "message": str(e)}), 400
            )

@app.route(rule="/producer/register", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {"topic": {"type": "string"}},
        "required": ["topic"],
    }
)
def register_producer():
    """Register a producer for a topic."""
    topic_name = request.get_json()["topic"]
    try:
        if not data_manager.check_topic_exists(topic_name):
            requests.post("http://primary:5000/topics",json = {"name":topic_name}).raise_for_status() 
        producer_id, partition_count = data_manager.add_producer(topic_name)
        return make_response(
            jsonify({
                "status": "success", 
                "producer_id": producer_id, 
                "partition_count":partition_count
            }),
            200,
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )

@app.route(rule="/consumer/register", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {"topic": {"type": "string"}},
        "required": ["topic"],
    }
)
def register_consumer():
    """Register a consumer for a topic."""
    topic_name = request.get_json()["topic"]

    try:
        consumer_id, partition_count = data_manager.add_consumer(topic_name)
        return make_response(
            jsonify({
                "status": "success", 
                "consumer_id": consumer_id, 
                "partition_count":partition_count}),
            200,
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )


@app.route(rule="/producer/produce", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "producer_id": {"type": "string"},
            "message": {"type": "string"},
            "partition_index": {"type":"number"},
        },
        "required": ["topic", "producer_id", "message"],
    }
)
def produce():
    """Add a log to a topic."""
    topic_name = request.get_json()["topic"]
    producer_id = request.get_json()["producer_id"]
    message = request.get_json()["message"]
    try:
        partition_index = None
        if "partition_index" in request.get_json():
            partition_index = request.get_json()["partition_index"]
        
        broker_host, partition_index = data_manager.get_broker_host(topic_name, producer_id, partition_index)
        log_index = data_manager.get_log_index(topic_name, partition_index)
        response = requests.post(
            "http://"+broker_host+":5000/producer/produce",
            json = {
                "topic": topic_name,
                "producer_id": producer_id,
                "message": message,
                "partition_index": partition_index,
                "log_index": log_index
            }
        )
        response.raise_for_status()
        data_manager.incr_partition_size(topic_name, partition_index)
        
        return make_response( 
            jsonify({"status": "success"}),
            200,
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )


@app.route(rule="/admin/broker/add", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "broker_host": {"type": "string"},
            "token": {"type": "string"},
        },
        "required": ["broker_host", "token"],
    }
)
def add_broker():
    """Add a broker"""
    broker_host = request.get_json()["broker_host"]
    token = request.get_json()["token"]

    if token != "rnn1234":  # replace with actual key!
        return make_response(
            jsonify({"status": "failure", "message": "Authentication failed"}), 400
        )
    try:
        data_manager.add_broker(broker_host)
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
    return make_response(jsonify({"status": "success",}),200)

@app.route(rule="/admin/broker/remove", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "broker_host": {"type": "string"},
            "token": {"type": "string"},
        },
        "required": ["broker_host", "token"],
    }
)
def remove_broker():
    """Remove a broker"""
    broker_host = request.get_json()["broker_host"]
    token = request.get_json()["token"]

    if token != "rnn1234":  # replace with actual key!
        return make_response(
            jsonify({"status": "failure", "message": "Authentication failed"}), 400
        )
    try:
        data_manager.remove_broker(broker_host)
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
    return make_response(jsonify({"status": "success",}),200)
    
@app.route(rule="/admin/broker/activate", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "broker_host": {"type": "string"},
            "token": {"type": "string"},
        },
        "required": ["broker_host", "token"],
    }
)
def activate_broker():
    """Activate a broker"""
    broker_host = request.get_json()["broker_host"]
    token = request.get_json()["token"]

    if token != "rnn1234":  # replace with actual key!
        return make_response(
            jsonify({"status": "failure", "message": "Authentication failed"}), 400
        )
    try:
        data_manager.activate_broker(broker_host)
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
    return make_response(jsonify({"status": "success",}),200)

@app.route(rule="/admin/broker/deactivate", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "broker_host": {"type": "string"},
            "token": {"type": "string"},
        },
        "required": ["broker_host", "token"],
    }
)
def deactivate_broker():
    """Deactivate a broker"""
    broker_host = request.get_json()["broker_host"]
    token = request.get_json()["token"]

    if token != "rnn1234":  # replace with actual key!
        return make_response(
            jsonify({"status": "failure", "message": "Authentication failed"}), 400
        )
    try:
        data_manager.deactivate_broker(broker_host)
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
    return make_response(jsonify({"status": "success",}),200)
