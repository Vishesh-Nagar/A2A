import logging
from dotenv import load_dotenv

load_dotenv()

from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.genai import types
from google.adk.tools.function_tool import FunctionTool
from utilities.discovery import DiscoveryClient
from agents.host_agent.agent_connect import AgentConnector

logger = logging.getLogger(__name__)


class GreetingAgent:
    """
    🧠 Orchestrator “meta-agent” that:
      - Provides two LLM tools: list_agents() and call_agent(...)
      - On a “greet me” request:
          1) Calls list_agents() to see which agents are up
          2) Calls call_agent("TellTimeAgent", "What is the current time?")
          3) Crafts a 2–3 line poetic greeting referencing that time
    """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        """
        🏗️ Constructor: build the internal orchestrator LLM, runner, discovery client.
        """

        self.orchestrator = self._build_orchestrator()

        self.user_id = "greeting_user"

        self.name = "Vishesh"

        self.runner = Runner(
            app_name=self.orchestrator.name,
            agent=self.orchestrator,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        self.discovery = DiscoveryClient()

        self.connectors: dict[str, AgentConnector] = {}

    def _build_orchestrator(self) -> LlmAgent:
        """
        🔧 Internal: define the LLM, its system instruction, and wrap tools.
        """

        async def list_agents() -> list[dict]:
            """
            Fetch all AgentCard metadata from the registry,
            return as a list of plain dicts.
            """

            cards = await self.discovery.list_agent_cards()

            return [card.model_dump(exclude_none=True) for card in cards]

        async def call_agent(agent_name: str, message: str) -> str:
            """
            Given an agent_name string and a user message,
            find that agent’s URL, send the task, and return its reply.
            """

            cards = await self.discovery.list_agent_cards()

            matched = next(
                (
                    c
                    for c in cards
                    if c.name.lower() == agent_name.lower()
                    or getattr(c, "id", "").lower() == agent_name.lower()
                ),
                None,
            )

            if not matched:
                matched = next(
                    (c for c in cards if agent_name.lower() in c.name.lower()), None
                )

            if not matched:
                raise ValueError(f"Agent '{agent_name}' not found.")

            key = matched.name

            if key not in self.connectors:
                self.connectors[key] = AgentConnector(
                    name=matched.name, base_url=matched.url, sender_agent="GreetingAgent"
                )
            connector = self.connectors[key]

            session_id = self.user_id

            task = await connector.send_task(message, session_id=session_id)

            if task.history and task.history[-1].parts:
                return task.history[-1].parts[0].text

            return ""

        system_instr = (
            "You have two tools:\n"
            "1) list_agents() → returns metadata for all available agents.\n"
            "2) call_agent(agent_name: str, message: str) → fetches a reply from that agent.\n"
            "When asked to greet, first call list_agents(), then "
            "call_agent('TellTimeAgent','What is the current time?'), "
            "then craft a 2–3 line poetic greeting referencing that time."
        )

        tools = [
            FunctionTool(list_agents),
            FunctionTool(call_agent),
        ]

        return LlmAgent(
            model="gemini-2.0-flash-001",
            name="greeting_orchestrator",
            description="Orchestrates time fetching and generates poetic greetings.",
            instruction=system_instr,
            tools=tools,
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """
        🔄 Public: return a hardcoded greeting.
        """

        return f"Hello {self.name}, how can I help you today?"
