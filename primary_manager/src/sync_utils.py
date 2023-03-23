import requests
import aiohttp
import os
from typing import Dict, Any

from src import AsyncRequests


async_request_handler = AsyncRequests()

async def _sync_broker_metadata(
    session: aiohttp.client.ClientSession, 
    route: str, 
    read_manager_index: int,
    project_name: str,
    json_data: Dict[str, Any]
):
    url = f"http://{project_name}-readonly_manager-{read_manager_index+1}:5000{route}"
    async with session.post(url, json=json_data) as response:
        response_status = response.status
        response_json = await response.json()
        return response_status, response_json

def sync_broker_metadata(
    route: str, 
    json_data: Dict[str, Any]
):
    read_only_count = int(os.environ["READ_REPLICAS"])
    project_name = os.environ["COMPOSE_PROJECT_NAME"]
    async_request_handler.run(
        _sync_broker_metadata, 
        [
            {
                "route": route, 
                "json_data": json_data, 
                "read_manager_index": read_manager_index,
                "project_name": project_name
            } for read_manager_index in range(read_only_count)
        ]
    )
