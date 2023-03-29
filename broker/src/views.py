from flask import make_response, request, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError

from src import app, master_queue, expects_json


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


@app.route(rule="/")
def index():
    return make_response("Welcome to Connectify Distributed Queue API!", 200)


@app.route(rule="/topics", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {"name": {"type": "string"}, "partition_index": {"type": "number"},"other_brokers":{"type":"array"}},
        "required": ["name","partition_index","other_brokers"],
    }
)
def topics():
    """Add a topic."""
    try:
        topic_name = request.get_json()["name"]
        partition_index = request.get_json()["partition_index"]
        other_brokers = request.get_json()["other_brokers"]
        master_queue.add_topic(topic_name, partition_index, other_brokers)
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
            jsonify({"status": "failure", "message": str(e)}),
            400,
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
            "log_index": {"type": "number"}
        },
        "required": ["topic", "producer_id", "message", "partition_index", "log_index"],
    }
)
def produce():
    """Add a log to a topic."""
    topic_name = request.get_json()["topic"]
    producer_id = request.get_json()["producer_id"]
    message = request.get_json()["message"]
    partition_index = request.get_json()["partition_index"]
    log_index = request.get_json()["log_index"]
    try:
        master_queue.add_log(log_index, topic_name, partition_index, producer_id, message)
        return make_response(
            jsonify({"status": "success"}),
            200,
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}),
            400,
        )


@app.route(rule="/consumer/consume", methods=["GET"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "partition_index": {"type": "number"},
            "log_index": {"type": "number"}
        },
        "required": ["topic", "partition_index", "log_index"],
    }
)
def consume():
    """Get a log from a topic."""
    topic_name = request.get_json()["topic"]
    partition_index = request.get_json()["partition_index"]
    log_index = request.get_json()["log_index"]
    try:
        log = master_queue.get_log(topic_name, partition_index, log_index)
        return make_response(
            jsonify({"status": "success", "message": log, "partition_read": partition_index}), 200
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}),
            400,
        )
