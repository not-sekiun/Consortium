import asyncio
from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from typing import TYPE_CHECKING, Protocol

from consortium.framework.agents.agent_capabilities._common_protocols import (
    _ResolveTimeoutProtocol,
)
from consortium.framework.agents.agent_capabilities.request_response_capability import (
    _TaskMessageHandlerProtocol,
)
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
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
    """Build an agent capability that exchanges a sequence of messages over several rounds.

    This is a factory that returns a new BaseAgentCapability subclass for interactions
    that require more than a single request-response exchange, such as chunked transfers
    or multi-step protocols. It repeatedly sends a message and awaits a reply until a
    handler signals completion or the iteration limit is reached. The result_handler and
    timeout_handler each return a (message, should_continue) tuple: returning False stops
    the loop and reports that message, while True sends the next message and continues.

    Args:
        name: Unique command name used to route task messages to this capability.
        description: Human-readable explanation of what the capability does.
        options: Configuration options the capability accepts, declared as a set.
        authors: Identifiers for the capability's authors.
        requires_admin: Whether the capability requires elevated privileges on the target.
        supported_oses: Platforms the capability supports. Defaults to any platform.
        mitre_attack_techniques: MITRE ATT&CK technique IDs associated with the capability.
        validating_function: Optional callable that validates the full resolved option set.
        timeout: Seconds to wait for each response before timing out. Ignored if
            resolve_timeout is provided.
        resolve_timeout: Optional callable that computes each round's response timeout
            dynamically from the current message and context, overriding timeout.
        iterations: Fixed maximum number of message exchanges. Ignored if
            resolve_iterations is provided; if neither is set the loop runs until a
            handler stops it.
        resolve_iterations: Optional callable that computes the maximum number of
            exchanges dynamically from the launch message and context.
        task_handler: Optional callable invoked before each message is sent, returning the
            message to transmit. May be sync or async.
        result_handler: Optional callable invoked with each response, returning a
            (message, should_continue) tuple. May be sync or async.
        timeout_handler: Optional callable invoked when a response times out, returning a
            (message, should_continue) tuple. May be sync or async.

    Returns:
        A new BaseAgentCapability subclass implementing the sequential exchange behavior.
    """

    async def _on_launch(
        self, task_message: TaskLaunchMessageModel
    ) -> TaskLaunchMessageModel | None:
        self._src_context = SimpleNamespace()
        context = self._src_context

        if iterations is not None:
            context.max_iterations = iterations
        elif resolve_iterations:
            context.max_iterations = resolve_iterations(
                task_message=task_message, context=context
            )
        else:
            context.max_iterations = None

        if task_handler:
            result = task_handler(
                agent=self.agent, task_message=task_message, context=context
            )
            if asyncio.iscoroutine(result):
                result = await result
            return result
        return task_message

    async def _on_execute(self) -> TaskOutputMessageModel:
        context = self._src_context
        current_message = self.launch_message
        index = 0

        while context.max_iterations is None or index < context.max_iterations:
            if resolve_timeout:
                recv_timeout = resolve_timeout(
                    task_message=current_message, context=context
                )
            else:
                recv_timeout = timeout

            try:
                result_message = await self.recv_from_agent(timeout=recv_timeout)
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
                    # Resend current message and try again
                    if task_handler:
                        current_message = task_handler(
                            agent=self.agent,
                            task_message=current_message,
                            context=context,
                        )
                        if asyncio.iscoroutine(current_message):
                            current_message = await current_message
                    await self.send_to_agent(task_message=current_message)
                    continue
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

            index += 1

            # Prepare and send the next message before looping back to recv
            if task_handler:
                current_message = task_handler(
                    agent=self.agent,
                    task_message=current_message,
                    context=context,
                )
                if asyncio.iscoroutine(current_message):
                    current_message = await current_message
            await self.send_to_agent(task_message=current_message)

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
            "on_launch": _on_launch,
            "on_execute": _on_execute,
        },
    )
