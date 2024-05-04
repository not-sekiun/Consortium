import queue
import uuid
from enum import StrEnum
from typing import Any

from consortium.server.models.agent_models import AgentResultModel, AgentTaskModel


class Agent:
    def __init__(
        self,
        name: str = "",
        agent_data: dict[str, Any] | None = None,
    ):
        if agent_data is None:
            agent_data = {}

        self.agent_id = uuid.uuid4()
        self.name = name
        self.agent_data = agent_data

        self._pending_tasks = queue.Queue()
        self._results = {}

    def add_pending_task(self, task: AgentTaskModel) -> None:
        self._pending_tasks.put(task)

    def get_next_pending_task(self) -> AgentTaskModel | None:
        if self._pending_tasks.empty():
            return None
        return self._pending_tasks.get()

    def add_result(self, result: AgentResultModel) -> None:
        self._results[str(result.result_id)] = result

    def get_result_by_result_id(self, result_id: str) -> AgentResultModel | None:
        return self._results.get(result_id, None)

    def get_all_results(self) -> list[AgentResultModel]:
        return list(self._results.values())

    def to_json(self) -> dict:
        return {
            "agent_id": str(self.agent_id),
        }

    def __repr__(self) -> str:
        return (
            f"Agent(name={self.name!r}, agent_id={self.agent_id!r}), "
            f"agent_data={self.agent_data!r})"
        )

    def __str__(self) -> str:
        return f'"{self.name}" ({self.agent_id})'
