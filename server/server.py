from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from models.agent import AgentCard
from models.request import A2ARequest, SendTaskRequest
from models.json_rpc import JSONRPCResponse, InternalError
from server import task_manager

import json
import logging

logger = logging.getLogger(__name__)

from datetime import datetime
from fastapi.encoders import jsonable_encoder


def json_serializer(obj):
    """
    This function can convert Python datetime objects to ISO strings.
    If you try to serialize a type it doesn't know, it will raise an error.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class A2AServer:
    def __init__(
        self,
        host="0.0.0.0",
        port=5000,
        agent_card: AgentCard = None,
        task_manager: task_manager = None,
    ):
        """
        🔧 Constructor for our A2AServer

        Args:
            host: IP address to bind the server to (default is all interfaces)
            port: Port number to listen on (default is 5000)
            agent_card: Metadata that describes our agent (name, skills, capabilities)
            task_manager: Logic to handle the task (using Gemini agent here)
        """
        self.host = host
        self.port = port
        self.agent_card = agent_card
        self.task_manager = task_manager

        self.app = Starlette()

        self.app.add_route("/", self._handle_request, methods=["POST"])

        self.app.add_route(
            "/.well-known/agent.json", self._get_agent_card, methods=["GET"]
        )

    def start(self):
        """
        Starts the A2A server using uvicorn (ASGI web server).
        This function will block and run the server forever.
        """
        if not self.agent_card or not self.task_manager:
            raise ValueError("Agent card and task manager are required")

        import uvicorn

        uvicorn.run(self.app, host=self.host, port=self.port)

    def _get_agent_card(self, request: Request) -> JSONResponse:
        """
        Endpoint for agent discovery (GET /.well-known/agent.json)

        Returns:
            JSONResponse: Agent metadata as a dictionary
        """
        return JSONResponse(self.agent_card.model_dump(exclude_none=True))

    async def _handle_request(self, request: Request):
        """
        This method handles task requests sent to the root path ("/").

        - Parses incoming JSON
        - Validates the JSON-RPC message
        - For supported task types, delegates to the task manager
        - Returns a response or error
        """
        try:

            body = await request.json()

            json_rpc = A2ARequest.validate_python(body)

            if isinstance(json_rpc, SendTaskRequest):
                result = await self.task_manager.on_send_task(json_rpc)
            else:
                raise ValueError(f"Unsupported A2A method: {type(json_rpc)}")

            return self._create_response(result)

        except Exception as e:
            logger.error(f"Exception: {e}")

            return JSONResponse(
                JSONRPCResponse(
                    id=None, error=InternalError(message=str(e))
                ).model_dump(),
                status_code=400,
            )

    def _create_response(self, result):
        """
        Converts a JSONRPCResponse object into a JSON HTTP response.

        Args:
            result: The response object (must be a JSONRPCResponse)

        Returns:
            JSONResponse: Starlette-compatible HTTP response with JSON body
        """
        if isinstance(result, JSONRPCResponse):

            return JSONResponse(
                content=jsonable_encoder(result.model_dump(exclude_none=True))
            )
        else:
            raise ValueError("Invalid response type")
