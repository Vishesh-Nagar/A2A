from pydantic import BaseModel
from typing import List


class AgentCapabilities(BaseModel):
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


class AgentSkill(BaseModel):
    id: str

    name: str

    description: str | None = None

    tags: List[str] | None = None

    examples: List[str] | None = None

    inputModes: List[str] | None = None

    outputModes: List[str] | None = None


class AgentCard(BaseModel):
    name: str

    description: str

    url: str

    version: str

    capabilities: AgentCapabilities

    skills: List[AgentSkill]
