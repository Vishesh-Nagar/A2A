from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Any, Literal, List
from datetime import datetime


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


Part = TextPart


class Message(BaseModel):
    role: Literal["user", "agent"]
    parts: List[Part]


class TaskStatus(BaseModel):
    state: str

    timestamp: datetime = Field(default_factory=datetime.now)


class Task(BaseModel):
    id: str
    status: TaskStatus
    history: List[Message]


class TaskIdParams(BaseModel):
    id: str
    metadata: dict[str, Any] | None = None


class TaskQueryParams(TaskIdParams):
    historyLength: int | None = None


class TaskSendParams(BaseModel):
    id: str

    sessionId: str = Field(default_factory=lambda: uuid4().hex)

    message: Message
    historyLength: int | None = None
    metadata: dict[str, Any] | None = None


class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    UNKNOWN = "unknown"
