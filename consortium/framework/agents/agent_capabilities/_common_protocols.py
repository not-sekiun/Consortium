from types import SimpleNamespace
from typing import TYPE_CHECKING, Protocol

from consortium.framework.agent_message_models import AgentTaskMessageModel

if TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent


class _ResolveTimeoutProtocol(Protocol):
    def __call__(
        self,
        agent: Agent,
        task_message: AgentTaskMessageModel,
        context: SimpleNamespace,
    ) -> int | float: ...
