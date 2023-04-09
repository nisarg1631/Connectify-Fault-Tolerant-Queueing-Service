from flask import make_response, request, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError
import logging
import requests

from src import app, ro_manager, expects_json


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

@app.route(rule="/topics", methods=["GET"])
def topics():
    """Return all the topics or add a topic."""
    try:
        topics = ro_manager.get_topics()
        return make_response(
            jsonify({"status": "success", "topics": topics}), 200
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
    

@app.route(rule="/consumer/consume", methods=["GET"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "partition_index": {"type": "number"},
            "consumer_id": {"type": "string"},
        },
        "required": ["topic", "consumer_id"],
    }
)
def consume():
    """Sanity check and assign consume request to a broker"""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    partition_index = None

    if "partition_index" in request.get_json():
        partition_index = request.get_json()["partition_index"]

    try:
        ro_manager.is_request_valid(topic_name, consumer_id, partition_index)

        if partition_index is None:
            partition_index, offset = ro_manager.get_partition_to_read_from(topic_name, consumer_id)
        else:
            offset = ro_manager.get_and_increment_consumer_offset(consumer_id, topic_name, partition_index)
        
        if offset is None:
            raise Exception("No messages to read from this partition")
        
        brokers = ro_manager.get_broker_hosts(topic_name, partition_index)

        for broker in brokers:
            try:
                response = requests.get(
                    f"http://{broker}:5000/consumer/consume",
                    json={
                        "topic": topic_name,
                        "partition_index": partition_index,
                        "log_index": offset,
                    },
                )
                response.raise_for_status()
                return make_response(response.json(), 200)
            except Exception as e:
                logging.error(f"Unable to serve the request from {broker}: {e}")
                continue
        
        raise Exception("Unable to serve this request")
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )

@app.route(rule="/size", methods=["GET"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "consumer_id": {"type": "string"},
            "partition_index": {"type": "number"}
        },
        "required": ["topic", "consumer_id"]
    }
)
def size():
    """Sanity check and assign size request to a broker."""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    partition_index = None

    if "partition_index" in request.get_json():
        partition_index = request.get_json()["partition_index"]

    try:
        ro_manager.is_request_valid(topic_name, consumer_id, partition_index)
        sizes = ro_manager.get_sizes(topic_name, consumer_id, partition_index)
        return make_response(
                jsonify({"status": "success", "sizes": sizes}), 200
            )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
