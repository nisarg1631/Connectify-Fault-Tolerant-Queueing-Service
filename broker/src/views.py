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
        "properties": {"name": {"type": "string"}, "partition_index": {"type": "number"}},
        "required": ["name","partition_index"],
    }
)
def topics():
    """Return all the topics or add a topic."""

    # If method is POST add a topic
    if request.method == "POST":
        topic_name = request.get_json()["name"]
        partition_index = request.get_json()["partition_index"]
    try:
        master_queue.add_topic(topic_name, partition_index)
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
        raise e

@app.route(rule="/consumer/register", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {"topic": {"type": "string"}, "consumer_id":{"type":"string"},"partition_index":{"type":"number"}},
        "required": ["topic","consumer_id","partition_index"],
    }
)
def register_consumer():
    """Register a consumer for a topic."""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    partition_index = request.get_json()["partition_index"]
    try:
        master_queue.add_consumer(topic_name,partition_index,consumer_id)
        return make_response(
            jsonify({"status": "success"}),
            200,
        )
    except Exception as e:
        raise

@app.route(rule="/producer/produce", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "producer_id": {"type": "string"},
            "message": {"type": "string"},
            "partition_index":{"type":"number"}
        },
        "required": ["topic", "producer_id", "message","partition_index"],
    }
)
def produce():
    """Add a log to a topic."""
    topic_name = request.get_json()["topic"]
    producer_id = request.get_json()["producer_id"]
    message = request.get_json()["message"]
    partition_index = request.get_json()["partition_index"]
    try:
        master_queue.add_log(topic_name, partition_index,producer_id, message)
        return make_response(
            jsonify({"status": "success"}),
            200,
        )
    except Exception as e:
        raise


@app.route(rule="/consumer/consume", methods=["GET"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "consumer_id": {"type": "string"},
            "partition_index": {"type": "number"}
        },
        "required": ["topic", "consumer_id", "partition_index"],
    }
)
def consume():
    """Consume a log from a topic."""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    partition_index = request.get_json()["partition_index"]
    try:
        log = master_queue.get_log(topic_name, partition_index, consumer_id)
        if log is not None:
            return make_response(
                jsonify({"status": "success", "message": log, "partition_read": partition_index}), 200
            )
        return make_response(
            jsonify(
                {"status": "failure", "message": "No logs available to pull."}
            ),
            200,
        )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}),
            400,
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
        "required": ["topic", "consumer_id"],
    }
)
def size():
    """Return the number of log messages in the requested topic for this consumer."""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    partition_index = None
    try:
        partition_index = int(request.get_json()["partition_index"])
    except:
        pass
    try:
        sizes = master_queue.get_size(consumer_id, topic_name, partition_index)
        return make_response(jsonify({"status": "success", "sizes": sizes}), 200)
    except Exception as e:
        raise