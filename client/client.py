import json
from uuid import uuid4
import httpx
from httpx_sse import connect_sse
from typing import Any
from models.request import SendTaskRequest, GetTaskRequest
from models.json_rpc import JSONRPCRequest
from models.task import Task, TaskSendParams
from models.agent import AgentCard

class A2AClientHTTPError(Exception):
    """Raised when an HTTP request fails (e.g., bad server response)"""
    pass

class A2AClientJSONError(Exception):
    """Raised when the response is not valid JSON"""
    pass

class A2AClient:
    def __init__(self, agent_card: AgentCard = None, url: str = None):
        """
        Initializes the client using either an agent card or a direct URL.
        One of the two must be provided.
        """
        if agent_card:
            self.url = agent_card.url
        elif url:
            self.url = url
        else:
            raise ValueError("Must provide either agent_card or url")

    async def send_task(self, payload: dict[str, Any]) -> Task:

        request = SendTaskRequest(id=uuid4().hex, params=TaskSendParams(**payload))

        print("\n📤 Sending JSON-RPC request:")
        print(json.dumps(request.model_dump(), indent=2))

        response = await self._send_request(request)
        return Task(**response["result"])

    async def get_task(self, payload: dict[str, Any]) -> Task:
        request = GetTaskRequest(params=payload)
        response = await self._send_request(request)
        return Task(**response["result"])

    async def _send_request(self, request: JSONRPCRequest) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.url, json=request.model_dump(), timeout=30
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                raise A2AClientHTTPError(e.response.status_code, str(e)) from e

            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e
