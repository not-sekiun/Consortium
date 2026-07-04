import asyncio
from collections.abc import Callable
from types import SimpleNamespace
from typing import final

from consortium.framework.agents.agent_capabilities._common_protocols import (
    _ResolveTimeoutProtocol,
)
from consortium.framework.agents.agent_capabilities.request_response_capability import (
    _TaskMessageHandlerProtocol,
)
from consortium.framework.agents.agent_capabilities.sequential_request_response_capability import (
    _ResolveIterationsProtocol,
    _SequentialResultMessagesHandlerProtocol,
    _SequentialTimeoutHandlerProtocol,
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


class SequentialRequestResponseCapability(BaseAgentCapability, abstract=True):
    """Template base class for capabilities that exchange messages over several rounds.

    This is the class-based counterpart to the sequential_request_response_capability
    factory, for interactions that need more than a single request-response exchange
    (chunked transfers, multi-step protocols, and so on). Subclass it, declare the usual
    capability metadata as class attributes, and override the hooks you need. The loop
    that repeatedly sends a message and awaits a reply lives in the final on_launch and
    on_execute methods.

    Two hooks drive the loop by returning a (message, should_continue) tuple: on_result
    for a received reply and on_timeout for a missed one. Returning should_continue as
    False stops the loop and reports that message; returning True sends the next message
    and continues. Intermediate state lives on self rather than a SimpleNamespace context.

    Attributes:
        timeout (int | float | None): Default number of seconds to wait for each
            response. None waits indefinitely. Override resolve_timeout for a per-round
            value.
        iterations (int | None): Fixed maximum number of message exchanges. None runs
            the loop until a hook stops it. Override resolve_iterations for a value
            computed from the launch message.
    """

    timeout: int | float | None = None
    iterations: int | None = None

    async def resolve_iterations(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> int | None:
        """Return the maximum number of message exchanges to perform.

        Override to compute the iteration cap dynamically from the launch message. The
        default returns the class-level iterations attribute.

        Args:
            task_message: The initial task message about to be launched.

        Returns:
            The maximum number of exchanges, or None to loop until a hook stops it.
        """
        return self.iterations

    async def resolve_timeout(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> int | float | None:
        """Return the number of seconds to wait for the next response.

        Override to compute the timeout dynamically per round from the message about to
        be sent. The default returns the class-level timeout attribute.

        Args:
            task_message: The message that was most recently sent to the agent.

        Returns:
            The receive timeout in seconds, or None to wait indefinitely.
        """
        return self.timeout

    async def on_task(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        """Inspect or mutate a message before it is sent on each round.

        Override to prepare the next outgoing message. The default returns it unchanged.

        Args:
            task_message: The message about to be sent.

        Returns:
            The message to transmit, or None to cancel the launch (first round only).
        """
        return task_message

    async def on_result(
        self,
        result_message: TaskOutputMessageModel,
    ) -> tuple[TaskOutputMessageModel, bool]:
        """Process a received response and decide whether to continue the loop.

        Override to inspect each reply. The default stops the loop and returns the reply.

        Args:
            result_message: The output message received from the agent this round.

        Returns:
            A (message, should_continue) tuple. When should_continue is False the loop
            stops and message is returned as the final result.
        """
        return result_message, False

    async def on_timeout(self) -> tuple[TaskOutputMessageModel | None, bool]:
        """Handle a missed response and decide whether to continue the loop.

        Override to recover from a timeout. The default re-raises the TimeoutError.

        Returns:
            A (message, should_continue) tuple. When should_continue is False and
            message is None the TimeoutError is re-raised; when False with a message the
            loop stops and returns it; when True the current message is resent and the
            loop continues.
        """
        # A bare raise re-raises the TimeoutError currently being handled in on_execute.
        raise

    @final
    async def on_launch(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        self._max_iterations = await self.resolve_iterations(task_message)
        return await self.on_task(task_message)

    @final
    async def on_execute(self) -> TaskOutputMessageModel:
        current_message = self.launch_message
        index = 0

        while self._max_iterations is None or index < self._max_iterations:
            recv_timeout = await self.resolve_timeout(current_message)

            try:
                result_message = await self.recv_from_agent(timeout=recv_timeout)
            except TimeoutError:
                result_message, should_continue = await self.on_timeout()
                if not should_continue:
                    if result_message is None:
                        raise  # Nothing to report, so propagate the timeout.
                    return result_message  # Stop and report the substitute message.
                # Resend the current message and retry without advancing the counter.
                current_message = await self.on_task(current_message)
                await self.send_to_agent(task_message=current_message)
                continue

            result_message, should_continue = await self.on_result(result_message)
            if not should_continue:
                return result_message

            index += 1

            # Prepare and send the next message before looping back to receive.
            current_message = await self.on_task(current_message)
            await self.send_to_agent(task_message=current_message)

        raise RuntimeError(
            "Maximum iterations reached without returning a final result message."
        )


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
    """Build a sequential capability from callbacks (compatibility wrapper).

    This preserves the original factory interface but is now a thin adapter over
    SequentialRequestResponseCapability: it generates a subclass whose hook methods
    delegate to the supplied callbacks, threading a per-instance SimpleNamespace context
    through them exactly as before. Prefer subclassing
    SequentialRequestResponseCapability directly; this wrapper exists for backwards
    compatibility and for generating capabilities programmatically.

    The callbacks map to hooks as follows: task_handler -> on_task,
    result_handler -> on_result, timeout_handler -> on_timeout,
    timeout/resolve_timeout -> resolve_timeout, and
    iterations/resolve_iterations -> resolve_iterations.

    Returns:
        A new BaseAgentCapability subclass implementing the sequential exchange behavior.
    """
    # Capture the callbacks under private names so the hook methods below can reference
    # them without shadowing this function's parameters.
    _timeout = timeout
    _resolve_timeout = resolve_timeout
    _iterations = iterations
    _resolve_iterations = resolve_iterations
    _task_handler = task_handler
    _result_handler = result_handler
    _timeout_handler = timeout_handler

    async def _resolve_iterations_hook(self, task_message):
        # Create the legacy context here (the first hook called) so it is shared across
        # every subsequent callback, mirroring the original factory.
        self._legacy_context = SimpleNamespace()
        context = self._legacy_context
        if _iterations is not None:
            context.max_iterations = _iterations
        elif _resolve_iterations:
            context.max_iterations = _resolve_iterations(
                task_message=task_message, context=context
            )
        else:
            context.max_iterations = None
        return context.max_iterations

    async def _resolve_timeout_hook(self, task_message):
        if _resolve_timeout:
            return _resolve_timeout(
                task_message=task_message, context=self._legacy_context
            )
        return _timeout

    async def _on_task_hook(self, task_message):
        if _task_handler:
            result = _task_handler(
                agent=self.agent,
                task_message=task_message,
                context=self._legacy_context,
            )
            if asyncio.iscoroutine(result):
                result = await result
            return result
        return task_message

    async def _on_result_hook(self, result_message):
        if _result_handler:
            result_tuple = _result_handler(
                agent=self.agent,
                result_message=result_message,
                context=self._legacy_context,
            )
            if asyncio.iscoroutine(result_tuple):
                result_tuple = await result_tuple
            return result_tuple
        return result_message, False

    async def _on_timeout_hook(self):
        if _timeout_handler:
            timeout_tuple = _timeout_handler(
                agent=self.agent, context=self._legacy_context
            )
            if asyncio.iscoroutine(timeout_tuple):
                timeout_tuple = await timeout_tuple
            return timeout_tuple
        raise

    return type(
        "SequentialRequestResponseCapability",
        (SequentialRequestResponseCapability,),
        {
            "name": name,
            "description": description,
            "options": options,
            "authors": authors,
            "requires_admin": requires_admin,
            "supported_oses": supported_oses,
            "mitre_attack_techniques": mitre_attack_techniques,
            "validating_function": validating_function,
            "timeout": timeout,
            "iterations": iterations,
            "resolve_iterations": _resolve_iterations_hook,
            "resolve_timeout": _resolve_timeout_hook,
            "on_task": _on_task_hook,
            "on_result": _on_result_hook,
            "on_timeout": _on_timeout_hook,
        },
    )
