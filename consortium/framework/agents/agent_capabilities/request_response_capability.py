import asyncio
from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from typing import TYPE_CHECKING, Protocol

from consortium.framework.agents.agent_capabilities._common_protocols import (
    _ResolveTimeoutProtocol,
)
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import (
    Failure,
    Success,
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
        task_message: TaskLaunchMessageModel,
        context: SimpleNamespace,
    ) -> TaskLaunchMessageModel | None | Awaitable[TaskLaunchMessageModel | None]: ...


class _ResultMessageHandlerProtocol(Protocol):
    def __call__(
        self,
        agent: Agent,
        result_message: TaskOutputMessageModel,
        context: SimpleNamespace,
    ) -> TaskOutputMessageModel | Awaitable[TaskOutputMessageModel]: ...


class _TimeoutHandlerProtocol(Protocol):
    def __call__(
        self,
        agent: Agent,
        context: SimpleNamespace,
    ) -> TaskOutputMessageModel | Awaitable[TaskOutputMessageModel]: ...


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
    mitre_attack_techniques: set[str] = None,
    validating_function: Callable | None = None,
    timeout: int | None = None,
    resolve_timeout: _ResolveTimeoutProtocol | None = None,
    task_handler: _TaskMessageHandlerProtocol | None = None,
    result_handler: _ResultMessageHandlerProtocol | None = None,
    timeout_handler: _TimeoutHandlerProtocol | None = None,
) -> type[BaseAgentCapability]:
    """Build an agent capability that sends one task message and awaits a single response.

    This is a factory that returns a new BaseAgentCapability subclass wired up with the
    supplied metadata and handlers, saving you from writing a full capability class for
    the common request-then-response pattern. The optional handlers let you hook into
    each phase: task_handler mutates the outgoing message, result_handler post-processes
    the agent's reply, and timeout_handler supplies a fallback result if the agent does
    not respond in time.

    Args:
        name: Unique command name used to route task messages to this capability.
        description: Human-readable explanation of what the capability does.
        options: Configuration options the capability accepts, declared as a set.
        authors: Identifiers for the capability's authors.
        requires_admin: Whether the capability requires elevated privileges on the target.
        supported_oses: Platforms the capability supports. Defaults to any platform.
        mitre_attack_techniques: MITRE ATT&CK technique IDs associated with the capability.
        validating_function: Optional callable that validates the full resolved option set.
        timeout: Seconds to wait for the agent's response before timing out. Ignored if
            resolve_timeout is provided.
        resolve_timeout: Optional callable that computes the response timeout dynamically
            from the launch message and context, overriding timeout.
        task_handler: Optional callable invoked before the message is sent, returning the
            message to transmit or None to cancel the launch. May be sync or async.
        result_handler: Optional callable invoked with the agent's response, returning the
            (possibly modified) output message. May be sync or async.
        timeout_handler: Optional callable invoked when the response times out, returning
            an output message to report instead of raising. May be sync or async.

    Returns:
        A new BaseAgentCapability subclass implementing the request-response behavior.
    """

    async def _on_launch(
        self, task_message: TaskLaunchMessageModel
    ) -> TaskLaunchMessageModel | None:
        self._rrc_context = SimpleNamespace()
        context = self._rrc_context

        if resolve_timeout:
            context.recv_timeout = resolve_timeout(
                task_message=task_message, context=context
            )
        else:
            context.recv_timeout = timeout

        if task_handler:
            result = task_handler(
                agent=self.agent, task_message=task_message, context=context
            )
            if asyncio.iscoroutine(result):
                result = await result
            return result
        return task_message

    async def _on_execute(self) -> Success | Failure:
        context = self._rrc_context

        try:
            result_message = await self.recv_from_agent(timeout=context.recv_timeout)
        except TimeoutError:
            if timeout_handler:
                result_message = timeout_handler(agent=self.agent, context=context)
                if asyncio.iscoroutine(result_message):
                    result_message = await result_message
                return (
                    Success(result_message)
                    if result_message.success
                    else Failure(result_message)
                )
            else:
                raise

        if result_handler:
            result_message = result_handler(
                agent=self.agent,
                result_message=result_message,
                context=context,
            )
            if asyncio.iscoroutine(result_message):
                result_message = await result_message

        if not isinstance(result_message, TaskOutputMessageModel):
            raise TypeError(
                "The `result_handler` must return an `TaskOutputMessageModel`."
            )

        return (
            Success(result_message)
            if result_message.success
            else Failure(result_message)
        )

    return type(
        "RequestResponseCapability",
        (BaseAgentCapability,),
        {
            "name": name,
            "description": description,
            "options": options,
            "authors": authors,
            "requires_admin": requires_admin,
            "mitre_attack_techniques": mitre_attack_techniques,
            "supported_oses": supported_oses,
            "validating_function": validating_function,
            "on_launch": _on_launch,
            "on_execute": _on_execute,
        },
    )
