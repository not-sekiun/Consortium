import uuid
from datetime import datetime
from typing import Any

from consortium.server.models.agent_models import (
    AgentResultModel,
    AgentTaskModel,
    AgentTaskState,
)


class Agent:
    def __init__(
        self,
        name: str = "",
        description: str = "",
        endpoint: str = "",
        agent_data: dict[str, Any] | None = None,
    ):
        if agent_data is None:
            agent_data = {}

        self.agent_id = uuid.uuid4()
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.agent_data = agent_data

        self.datetime_first_checked_in = datetime.now()
        self.datetime_last_checked_in = datetime.now()

        # TODO: Consider moving all the tasks and results to a database instead of
        #  storing them all in memory. Storing the tasks and results for an agent might
        #  get very unwieldy memory wise as the framework scales. Will have to check
        #  with a benchmark.
        self._queued_tasks = {}
        self._running_tasks = {}
        self._completed_tasks = {}
        self._results = {}

    def add_task(self, task: AgentTaskModel) -> None:
        self._queued_tasks[str(task.task_id)] = task

    def get_next_queued_task(self) -> list[AgentTaskModel] | None:
        if not self._queued_tasks:
            return None

        for task in self._queued_tasks.values():
            del [self._queued_tasks[str(task.task_id)]]
            # The moment a task is removed from the queued_tasks dictionary, it is
            # considered to be running.
            task.state = AgentTaskState.RUNNING
            self._running_tasks[str(task.task_id)] = task
            return task

    # This function is one which returns a list of tasks but doesn't actually remove
    # them from the queued tasks list or consider them to be running once returned. It
    # is purely used just to look at the current state of a queued task.
    def peek_all_queued_tasks(self) -> list[AgentTaskModel]:
        return list(self._queued_tasks)

    def peek_queued_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        try:
            return self._queued_tasks[task_id]
        except KeyError:
            raise ValueError(
                f'No queued task exists with the provided task ID "{task_id}"',
            )

    def get_all_running_tasks(self) -> list[AgentTaskModel]:
        return list(self._running_tasks)

    def get_running_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        try:
            return self._running_tasks[task_id]
        except KeyError:
            raise ValueError(
                f'No running task exists with the provided task ID "{task_id}"',
            )

    def get_all_completed_tasks(self) -> list[AgentTaskModel]:
        return list(self._completed_tasks)

    def get_completed_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        try:
            return self._completed_tasks[task_id]
        except KeyError:
            raise ValueError(
                f'No completed task exists with the provided task ID "{task_id}"',
            )

    def get_all_tasks(self) -> list[AgentTaskModel]:
        return [
            *self._queued_tasks.values(),
            *self._running_tasks.values(),
            *self._completed_tasks.values(),
        ]

    def get_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        all_tasks = self.get_all_tasks()
        for task in all_tasks:
            if task_id == task.task_id:
                return task
        raise ValueError(f'No task exists with the provided task ID "{task_id}"')

    def add_result(self, result: AgentResultModel) -> None:
        if result.task_id not in self._running_tasks:
            raise ValueError(
                f'No task exists with the provided task ID "{result.task_id}" from the '
                f"provided result",
            )
        self._results[str(result.result_id)] = result

    def get_all_results(self) -> list[AgentResultModel]:
        return list(self._results.values())

    def get_all_successful_results(self) -> list[AgentResultModel]:
        return [
            result for result in self._results.values() if result.status == "SUCCESS"
        ]

    def get_all_failed_results(self) -> list[AgentResultModel]:
        return [result for result in self._results.values() if result.status == "FAIL"]

    def get_all_errored_results(self) -> list[AgentResultModel]:
        return [result for result in self._results.values() if result.status == "ERROR"]

    def get_result_by_task_id(self, task_id: str) -> AgentResultModel:
        for result in self._results.values():
            if result.task_id == task_id:
                return result
        raise ValueError(
            f"No result exists that is associated with the provided task ID: {task_id}",
        )

    def get_result_by_result_id(self, result_id: str) -> AgentResultModel:
        try:
            return self._results[result_id]
        except KeyError:
            raise ValueError(
                f"No result exists with the provided result ID: {result_id}",
            )

    def register_checked_in(self) -> None:
        self.datetime_last_checked_in = datetime.now()

    def to_json(self) -> dict:
        return {
            "agent_id": str(self.agent_id),
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "agent_data": self.agent_data,
            "datetime_first_checked_in": self.datetime_first_checked_in.isoformat(),
            "datetime_last_checked_in": self.datetime_last_checked_in.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"Agent(name={self.name!r}, description={self.description!r}), "
            f"agent_data={self.agent_data!r})"
        )

    def __str__(self) -> str:
        return f'"{self.name}" ({self.agent_id})'
