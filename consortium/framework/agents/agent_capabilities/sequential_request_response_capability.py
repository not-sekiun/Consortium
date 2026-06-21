import asyncio
from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from typing import TYPE_CHECKING, Protocol

from consortium.framework.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_capabilities._common_protocols import (
    _ResolveTimeoutProtocol,
)
from consortium.framework.agents.agent_capabilities.request_response_capability import (
    _TaskMessageHandlerProtocol,
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


class _SequentialResultMessagesHandlerProtocol(Protocol):
    def __call__(
        self,
        agent: Agent,
        result_message: TaskOutputMessageModel,
        context: SimpleNamespace,
    ) -> (
        tuple[TaskOutputMessageModel, bool]
        | Awaitable[tuple[TaskOutputMessageModel, bool]]
    ): ...


class _SequentialTimeoutHandlerProtocol(Protocol):
    def __call__(
        self,
        agent: Agent,
        context: SimpleNamespace,
    ) -> (
        tuple[TaskOutputMessageModel | None, bool]
        | Awaitable[tuple[TaskOutputMessageModel | None, bool]]
    ): ...


class _ResolveIterationsProtocol(Protocol):
    def __call__(
        self,
        task_message: TaskLaunchMessageModel,
        context: SimpleNamespace,
    ) -> int: ...


def sequential_request_response_capability(
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
    timeout: int | float | None = None,
    resolve_timeout: _ResolveTimeoutProtocol | None = None,
    iterations: int | None = None,
    resolve_iterations: _ResolveIterationsProtocol | None = None,
    task_handler: _TaskMessageHandlerProtocol | None = None,
    result_handler: _SequentialResultMessagesHandlerProtocol | None = None,
    timeout_handler: _SequentialTimeoutHandlerProtocol | None = None,
) -> type[BaseAgentCapability]:
    async def _execute(
        self, task_message: TaskLaunchMessageModel
    ) -> TaskOutputMessageModel:
        context = SimpleNamespace()

        index = 0
        if iterations is not None:
            max_iterations = iterations
        elif resolve_iterations:
            max_iterations = resolve_iterations(
                task_message=task_message, context=context
            )
        else:
            max_iterations = None

        while max_iterations is None or index < max_iterations:
            if resolve_timeout:
                send_and_recv_timeout = resolve_timeout(
                    task_message=task_message, context=context
                )
            else:
                send_and_recv_timeout = timeout

            if task_handler:
                task_message = task_handler(
                    agent=self.agent, task_message=task_message, context=context
                )
                if asyncio.iscoroutine(task_message):
                    task_message = await task_message

            try:
                result_message = await self.send_and_recv_from_agent(
                    task_message=task_message,
                    timeout=send_and_recv_timeout,
                )
            except TimeoutError:
                if timeout_handler:
                    timeout_tuple = timeout_handler(agent=self.agent, context=context)
                    if asyncio.iscoroutine(timeout_tuple):
                        timeout_tuple = await timeout_tuple

                    result_message, should_continue = timeout_tuple
                    if not should_continue:
                        if result_message is None:
                            raise  # Do not continue, no message to report, so raise error
                        return result_message  # Do not continue, return a message to report
                    else:
                        continue  # Continue, whether we have a message to report or not we continue
                else:
                    raise

            if result_handler:
                result_tuple = result_handler(
                    agent=self.agent, result_message=result_message, context=context
                )
                if asyncio.iscoroutine(result_tuple):
                    result_tuple = await result_tuple

                result_message, should_continue = result_tuple
                if not should_continue:
                    return result_message
            else:
                return result_message

        raise RuntimeError(
            "Maximum iterations reached without returning a final result message."
        )

    return type(
        "SequentialRequestResponseCapability",
        (BaseAgentCapability,),
        {
            "name": name,
            "description": description,
            "options": options,
            "authors": authors,
            "requires_admin": requires_admin,
            "supported_oses": supported_oses,
            "mitre_attack_techniques": mitre_attack_techniques,
            "validating_function": validating_function,
            "execute": _execute,
        },
    )
