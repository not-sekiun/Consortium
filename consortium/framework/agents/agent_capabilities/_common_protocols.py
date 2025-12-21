from types import SimpleNamespace
from typing import Protocol

from consortium.framework.agent_message_models import AgentTaskMessageModel


class _ResolveTimeoutProtocol(Protocol):
    def __call__(
        self,
        task_message: AgentTaskMessageModel,
        context: SimpleNamespace,
    ) -> int | float: ...
