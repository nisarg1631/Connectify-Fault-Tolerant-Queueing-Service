from flask import make_response, request, jsonify
from flask_expects_json import expects_json
from jsonschema import ValidationError
import logging

from src import app, ro_manager, requests, expects_json


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
def consume(): # HEALTHCHECK
    """Sanity check and assign consume request to a broker"""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    partition_index: int = None
    read_from_given_partition = False

    try:
        partition_index = int(request.get_json()["partition_index"])
        try:
            ro_manager.is_request_valid(topic_name, consumer_id, partition_index)
        except Exception as e:
            return make_response(
                jsonify({"status": "failure", "message": str(e)}), 400
            )
        read_from_given_partition = True
    except Exception as e:
        try:
            ro_manager.is_request_valid(topic_name, consumer_id)
        except Exception as e:
            return make_response(
                jsonify({"status": "failure", "message": str(e)}), 400
            )
        partition_index = ro_manager.find_best_partition(topic_name, consumer_id)

    try:
        num_tries = 0
        response = None
        success = False
        found_active_broker = False
        num_partitions = ro_manager.get_partition_count(topic_name)
        # Try all brokers once, and infer no logs to read only if all brokers say so
        while num_tries < num_partitions:
            broker_host = ro_manager.get_broker_host(topic_name, partition_index)[0]
            # Add partition_index to the request data
            json_data = request.get_json()
            json_data["partition_index"] = partition_index
            # Forward this request to a broker, wait for a response
            if ro_manager.broker_is_active(broker_host):
                try:
                    response = requests.get(
                        url = "http://"+broker_host+":5000/consumer/consume",
                        json = json_data
                    )
                    # Check response received from broker, if success, then exit loop
                    if(response.json()["status"] == "success"):
                        success = True
                        found_active_broker = True
                        break
                    found_active_broker = True
                except Exception as e:
                    # Broker is not active, try next broker
                    pass
            num_tries += 1
            partition_index = (partition_index + 1) % num_partitions
            # If consumer wanted to read from given partition only, then exit loop
            if read_from_given_partition == True and num_tries == 1:
                break
        # Reply to consumer
        if found_active_broker:
            response_dict = {"status": response.json()["status"], "message": response.json()["message"]}
            if success:
                response_dict["partition_read"] = response.json()["partition_read"] 
            return make_response(
                jsonify(response_dict), 200
            )
        else:
            return make_response(
                jsonify({"status": "failure", "message": "No active brokers found"}), 400
            )
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
def size(): # HEALTHCHECK
    """Sanity check and assign size request to a broker."""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    partition_index = None
    try:
        partition_index = int(request.get_json()["partition_index"])
        try:
            ro_manager.is_request_valid(topic_name, consumer_id, partition_index)
        except Exception as e:
            return make_response(
                jsonify({"status": "failure", "message": str(e)}), 400
            )
    except Exception as e:
        try:
            ro_manager.is_request_valid(topic_name, consumer_id)
        except Exception as e:
            return make_response(
                jsonify({"status": "failure", "message": str(e)}), 400
            )
    
    try:
        sizes = []
        # Contact each broker that contains partitions of the given topic. If
        # partition number is given only that broker that contains the partition
        # is contacted.
        success = False
        for broker_host in ro_manager.get_broker_host(topic_name, partition_index):
            # Forward this request to the broker, wait for a response
            if ro_manager.broker_is_active(broker_host):
                try:
                    response = requests.get(
                        url = "http://"+broker_host+":5000/size",
                        json = request.get_json()
                    )
                    sizes.extend(list(response.json()["sizes"]))
                    success = True
                except Exception as e:
                    pass
        # Reply to consumer
        if success:
            return make_response(
                jsonify({"status": "success", "sizes": sizes}), 200
            )
        else:
            return make_response(
                jsonify({"status": "failure", "message": "No brokers available"}), 400
            )
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )


# endpoints for syncing between primary and read only managers

@app.route(rule="/sync/topics", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {"name": {"type": "string"},"number_of_partitions":{"type":"number"},"broker_list":{"type":"array"}},
        "required": ["name","number_of_partitions","broker_list"],
    },
)
def sync_topics():
    """Add new topic to loaded memory"""
    
    topic_name = request.get_json()["name"]
    number_of_partitions = request.get_json()["number_of_partitions"]
    broker_list = request.get_json()["broker_list"]
    try:
        ro_manager.add_topic(topic_name,number_of_partitions,broker_list)
        return make_response(
                jsonify(
                    {
                        "status": "success"
                    }
                ),
                200,
        )
    except Exception as e:
        return make_response(
                jsonify({"status": "failure", "message": str(e)}), 400
            )

@app.route(rule="/sync/consumer/register", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {"topic": {"type": "string"}, "consumer_id":{"type":"string"}},
        "required": ["topic","consumer_id"],
    }
)
def sync_register_consumer():
    """Register a consumer for a topic in loaded memory"""
    topic_name = request.get_json()["topic"]
    consumer_id = request.get_json()["consumer_id"]
    try:
        ro_manager.add_consumer_to_topic(topic_name, consumer_id)   
        return make_response(
                jsonify(
                    {
                        "status": "success",
                    }
                ),
                200,
        )  
    except Exception as e:
        raise

@app.route(rule="/sync/broker/add", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "broker_host": {"type": "string"},
        },
        "required": ["broker_host"],
    }
)
def add_broker():
    """Add a broker"""
    broker_host = request.get_json()["broker_host"]

    try:
        ro_manager.add_broker(broker_host)
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
    return make_response(jsonify({"status": "success",}),200,)

@app.route(rule="/admin/broker/remove", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "broker_host": {"type": "string"},
        },
        "required": ["broker_host"],
    }

)
def remove_broker():
    """Remove a broker"""
    broker_host = request.get_json()["broker_host"]
    try:
        ro_manager.remove_broker(broker_host)
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
    return make_response(jsonify({"status": "success",}),200,)
    
@app.route(rule="/sync/broker/activate", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "broker_host": {"type": "string"},
        },
        "required": ["broker_host"],
    }
)
def activate_broker():
    """Activate a broker"""
    broker_host = request.get_json()["broker_host"]
    try:
        ro_manager.activate_broker(broker_host)
    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
    return make_response(jsonify({"status": "success",}),200,)

@app.route(rule="/sync/broker/deactivate", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "broker_host": {"type": "string"},
        },
        "required": ["broker_host"],
    }
)
def deactivate_broker():
    """Deactivate a broker"""
    broker_host = request.get_json()["broker_host"]
    try:
        ro_manager.deactivate_broker(broker_host)

    except Exception as e:
        return make_response(
            jsonify({"status": "failure", "message": str(e)}), 400
        )
    return make_response(jsonify({"status": "success",}),200,)