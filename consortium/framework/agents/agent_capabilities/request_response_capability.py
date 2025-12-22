import asyncio
from collections.abc import Awaitable
from types import SimpleNamespace
from typing import TYPE_CHECKING, Protocol

from consortium.framework.agent_message_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.framework.agents.agent_capabilities._common_protocols import (
    _ResolveTimeoutProtocol,
)
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
    SupportedOS,
)
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)

if TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent


class _TaskMessageHandlerProtocol(Protocol):
    def __call__(
        self,
        agent: Agent,
        task_message: AgentTaskMessageModel,
        context: SimpleNamespace,
    ) -> AgentTaskMessageModel | Awaitable[AgentTaskMessageModel]: ...


class _ResultMessageHandlerProtocol(Protocol):
    def __call__(
        self,
        agent: Agent,
        result_message: AgentResultMessageModel,
        context: SimpleNamespace,
    ) -> AgentResultMessageModel | Awaitable[AgentResultMessageModel]: ...


class _TimeoutHandlerProtocol(Protocol):
    def __call__(
        self,
        agent: Agent,
        context: SimpleNamespace,
    ) -> AgentResultMessageModel | Awaitable[AgentResultMessageModel]: ...


def request_response_capability(
    name: str,
    description: str = "",
    options: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ] = None,
    authors: set[str] = None,
    requires_admin: bool = False,
    supported_oses: set[SupportedOS] = None,
    timeout: int | None = None,
    resolve_timeout: _ResolveTimeoutProtocol | None = None,
    task_handler: _TaskMessageHandlerProtocol | None = None,
    result_handler: _ResultMessageHandlerProtocol | None = None,
    timeout_handler: _TimeoutHandlerProtocol | None = None,
) -> type[BaseAgentCapability]:
    async def _execute(
        self, agent: Agent, task_message: AgentTaskMessageModel
    ) -> AgentResultMessageModel:
        context = SimpleNamespace()

        if resolve_timeout:
            send_and_recv_timeout = resolve_timeout(
                agent=agent, task_message=task_message, context=context
            )
        else:
            send_and_recv_timeout = timeout

        if task_handler:
            task_message = task_handler(
                agent=agent, task_message=task_message, context=context
            )
            if asyncio.iscoroutine(task_message):
                task_message = await task_message

        try:
            result_message = await self.send_and_recv_from_agent(
                task_message=task_message, timeout=send_and_recv_timeout
            )
        except TimeoutError:
            if timeout_handler:
                result_message = timeout_handler(agent=agent, context=context)
                if asyncio.iscoroutine(result_message):
                    result_message = await result_message
                return result_message
            else:
                raise

        if result_handler:
            result_message = result_handler(
                agent=agent,
                result_message=result_message,
                context=context,
            )
            if asyncio.iscoroutine(result_message):
                result_message = await result_message

        if not isinstance(result_message, AgentResultMessageModel):
            raise TypeError(
                "The `result_handler` must return an `AgentResultMessageModel`."
            )

        return result_message

    return type(
        "RequestResponseCapability",
        (BaseAgentCapability,),
        {
            "name": name,
            "description": description,
            "options": options,
            "authors": authors,
            "requires_admin": requires_admin,
            "supported_oses": supported_oses,
            "execute": _execute,
        },
    )
