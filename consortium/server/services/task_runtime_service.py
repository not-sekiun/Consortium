import uuid
from typing import TYPE_CHECKING

from loguru import logger

from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.task_runtime import TaskRuntime

if TYPE_CHECKING:
    from consortium.framework.agents._task_messages_queue import TaskMessagesQueue


def _canonicalize_uuid(value: str | uuid.UUID) -> str | None:
    # Runtime entries are keyed by canonical lowercase UUID strings so that a lookup
    # made with a raw string matches an entry attached with a UUID object. Returns None
    # when the value is not a UUID at all, which callers treat as "no such runtime"
    # rather than as an error.
    try:
        return str(uuid.UUID(str(value)))
    except ValueError:
        return None


class TaskRuntimeService:
    # Owns the ephemeral execution state of a task (its handler and message queues),
    # which lives only as long as the owning agent. This is deliberately separate from
    # TasksService, which owns task records that outlive their agent.
    def __init__(self):
        self._runtimes: dict[str, TaskRuntime] = {}
        # A dict acts as an ordered set. The first task ID for an agent is its earliest
        # live runtime, which preserves the sequential muxer's ordering policy.
        self._agent_task_ids: dict[str, dict[str, None]] = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

    def __str__(self):
        return "TaskRuntimeService"

    def __repr__(self):
        return "TaskRuntimeService()"

    def attach_task_runtime(
        self,
        task_id: str | uuid.UUID,
        agent_id: str | uuid.UUID,
        task_runtime: TaskRuntime,
    ) -> None:
        normalized_task_id = _canonicalize_uuid(value=task_id)
        normalized_agent_id = _canonicalize_uuid(value=agent_id)
        if normalized_task_id is None or normalized_agent_id is None:
            return

        self._runtimes[normalized_task_id] = task_runtime
        self._agent_task_ids.setdefault(normalized_agent_id, {})[normalized_task_id] = (
            None
        )
        self._logger.debug(
            "Attached runtime for task {} owned by agent {}",
            normalized_task_id,
            normalized_agent_id,
        )

    def get_task_runtime(self, task_id: str | uuid.UUID) -> TaskRuntime | None:
        normalized_task_id = _canonicalize_uuid(value=task_id)
        if normalized_task_id is None:
            return None
        return self._runtimes.get(normalized_task_id)

    def pop(self, task_id: str | uuid.UUID) -> TaskRuntime | None:
        normalized_task_id = _canonicalize_uuid(value=task_id)
        if normalized_task_id is None:
            return None

        runtime = self._runtimes.pop(normalized_task_id, None)
        for agent_id, task_ids in list(self._agent_task_ids.items()):
            if normalized_task_id not in task_ids:
                continue
            task_ids.pop(normalized_task_id, None)
            if not task_ids:
                self._agent_task_ids.pop(agent_id, None)
            break

        if runtime is not None:
            self._logger.debug("Detached runtime for task {}", normalized_task_id)
        return runtime

    def pop_all_for_agent(self, agent_id: str | uuid.UUID) -> list[TaskRuntime]:
        normalized_agent_id = _canonicalize_uuid(value=agent_id)
        if normalized_agent_id is None:
            return []

        task_ids = self._agent_task_ids.pop(normalized_agent_id, {})
        runtimes = [
            runtime
            for task_id in task_ids
            if (runtime := self._runtimes.pop(task_id, None)) is not None
        ]
        if runtimes:
            self._logger.debug(
                "Detached {} runtime(s) owned by agent {}",
                len(runtimes),
                normalized_agent_id,
            )
        return runtimes

    def first_readable_task_id_for_agent(self, agent_id: str | uuid.UUID) -> str | None:
        normalized_agent_id = _canonicalize_uuid(value=agent_id)
        if normalized_agent_id is None:
            return None

        for task_id in list(self._agent_task_ids.get(normalized_agent_id, {})):
            runtime = self._runtimes.get(task_id)
            if runtime is None:
                self._discard_agent_task_id(
                    agent_id=normalized_agent_id,
                    task_id=task_id,
                )
                continue
            if runtime.has_readable_outbox():
                return task_id
            if runtime.outbox is not None:
                self.release_outbox(task_id=task_id)
        return None

    def readable_outboxes_for_agent(
        self, agent_id: str | uuid.UUID
    ) -> list[tuple[str, TaskMessagesQueue]]:
        normalized_agent_id = _canonicalize_uuid(value=agent_id)
        if normalized_agent_id is None:
            return []

        readable_outboxes = []
        for task_id in list(self._agent_task_ids.get(normalized_agent_id, {})):
            runtime = self._runtimes.get(task_id)
            if runtime is None:
                self._discard_agent_task_id(
                    agent_id=normalized_agent_id,
                    task_id=task_id,
                )
                continue

            outbox = runtime.outbox
            if outbox is None:
                continue
            if not runtime.has_readable_outbox():
                self.release_outbox(task_id=task_id)
                continue
            readable_outboxes.append((task_id, outbox))
        return readable_outboxes

    def has_readable_outbox_for_agent(self, agent_id: str | uuid.UUID) -> bool:
        return self.first_readable_task_id_for_agent(agent_id=agent_id) is not None

    def release_handler(self, task_id: str | uuid.UUID) -> None:
        runtime = self.get_task_runtime(task_id=task_id)
        if runtime is None:
            return
        runtime.release_handler()
        self._pop_if_exhausted(task_id=task_id, runtime=runtime)

    def release_inbox(self, task_id: str | uuid.UUID) -> None:
        runtime = self.get_task_runtime(task_id=task_id)
        if runtime is None:
            return
        runtime.release_inbox()
        self._pop_if_exhausted(task_id=task_id, runtime=runtime)

    def release_outbox(self, task_id: str | uuid.UUID) -> None:
        runtime = self.get_task_runtime(task_id=task_id)
        if runtime is None:
            return
        runtime.release_outbox()
        self._pop_if_exhausted(task_id=task_id, runtime=runtime)

    def _pop_if_exhausted(
        self,
        task_id: str | uuid.UUID,
        runtime: TaskRuntime,
    ) -> None:
        if runtime.is_exhausted():
            self.pop(task_id=task_id)

    def _discard_agent_task_id(self, agent_id: str, task_id: str) -> None:
        task_ids = self._agent_task_ids.get(agent_id)
        if task_ids is None:
            return
        task_ids.pop(task_id, None)
        if not task_ids:
            self._agent_task_ids.pop(agent_id, None)
