from types import SimpleNamespace
from typing import Protocol

from consortium.framework.agents.agent_message_models import TaskLaunchMessageModel


class _ResolveTimeoutProtocol(Protocol):
    def __call__(
        self,
        task_message: TaskLaunchMessageModel,
        context: SimpleNamespace,
    ) -> int | float: ...
