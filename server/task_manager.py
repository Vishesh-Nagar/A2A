from abc import (
    ABC,
    abstractmethod,
)
from typing import Dict
import asyncio
from models.request import (
    SendTaskRequest,
    SendTaskResponse,
    GetTaskRequest,
    GetTaskResponse,
)
from models.task import (
    Task,
    TaskSendParams,
    TaskQueryParams,
    TaskStatus,
    TaskState,
    Message,
)

class TaskManager(ABC):
    """
    🔧 This is a base interface class.

    All Task Managers must implement these two async methods:
    - on_send_task(): to receive and process new tasks
    - on_get_task(): to fetch the current status or conversation history of a task

    This makes sure all implementations follow a consistent structure.
    """

    @abstractmethod
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """📥 This method will handle new incoming tasks."""
        pass

    @abstractmethod
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        """📤 This method will return task details by task ID."""
        pass


class InMemoryTaskManager(TaskManager):
    """
    🧠 A simple, temporary task manager that stores everything in memory (RAM).

    Great for:
    - Demos
    - Local development
    - Single-session interactions

    ❗ Not for production: Data is lost when the app stops or restarts.
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.lock = asyncio.Lock()

    async def upsert_task(self, params: TaskSendParams) -> Task:
        """
        Create a new task if it doesn’t exist, or update the history if it does.

        Args:
            params: TaskSendParams – includes task ID, session ID, and message

        Returns:
            Task – the newly created or updated task
        """
        async with self.lock:
            task = self.tasks.get(params.id)

            if task is None:

                task = Task(
                    id=params.id,
                    status=TaskStatus(state=TaskState.SUBMITTED),
                    history=[params.message],
                )
                self.tasks[params.id] = task
            else:

                task.history.append(params.message)

            return task

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        This method is intentionally not implemented here.
        Subclasses like `AgentTaskManager` should override it.

        Raises:
            NotImplementedError: if someone tries to use it directly
        """
        raise NotImplementedError("on_send_task() must be implemented in subclass")

    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        """
        Look up a task using its ID, and optionally return only recent messages.

        Args:
            request: A GetTaskRequest with an ID and optional history length

        Returns:
            GetTaskResponse – contains the task if found, or an error message
        """
        async with self.lock:
            query: TaskQueryParams = request.params
            task = self.tasks.get(query.id)

            if not task:

                return GetTaskResponse(
                    id=request.id, error={"message": "Task not found"}
                )

            task_copy = task.model_copy()
            if query.historyLength is not None:
                task_copy.history = task_copy.history[-query.historyLength :]
            else:
                task_copy.history = task_copy.history

            return GetTaskResponse(id=request.id, result=task_copy)
