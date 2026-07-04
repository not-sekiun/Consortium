import asyncio
from collections.abc import Callable
from types import SimpleNamespace
from typing import final

from consortium.framework.agents.agent_capabilities._common_protocols import (
    _ResolveTimeoutProtocol,
)
from consortium.framework.agents.agent_capabilities.request_response_capability import (
    _ResultMessageHandlerProtocol,
    _TaskMessageHandlerProtocol,
    _TimeoutHandlerProtocol,
)
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
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


class RequestResponseCapability(BaseAgentCapability, abstract=True):
    """Template base class for capabilities that send one task and await one response.

    This is the class-based counterpart to the request_response_capability factory.
    Subclass it, declare the usual capability metadata as class attributes (name,
    description, options, and so on), and override only the hooks you need. The
    request-then-response machinery, including timeout handling, lives in the final
    on_launch and on_execute methods so subclasses never have to reimplement it.

    Intermediate state that used to be threaded through a SimpleNamespace context is
    now just instance state on self, and the agent is always available as self.agent.

    Attributes:
        timeout (int | float | None): Default number of seconds to wait for the agent's
            response. None waits indefinitely. Override resolve_timeout for a value
            computed per task.

    Example: A capability that trims the agent's response
        ```python
        class Whoami(RequestResponseCapability):
            name = "whoami"
            description = "Return the current user."
            timeout = 30

            async def on_result(self, result_message):
                result_message.message = result_message.message.strip()
                return result_message
        ```
    """

    timeout: int | float | None = None

    async def resolve_timeout(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> int | float | None:
        """Return the number of seconds to wait for the agent's response.

        Override to compute the timeout dynamically from the outgoing task message.
        The default returns the class-level timeout attribute.

        Args:
            task_message: The task message about to be sent to the agent.

        Returns:
            The receive timeout in seconds, or None to wait indefinitely.
        """
        return self.timeout

    async def on_task(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        """Inspect or mutate the task message before it is sent to the agent.

        Override to enrich or replace the outgoing message. The default returns it
        unchanged.

        Args:
            task_message: The task message prepared for launch.

        Returns:
            The message to transmit, or None to cancel the launch.
        """
        return task_message

    async def on_result(
        self,
        result_message: TaskOutputMessageModel,
    ) -> TaskOutputMessageModel:
        """Post-process the agent's response before it becomes the outcome.

        Override to reshape or annotate the response. The default returns it unchanged.

        Args:
            result_message: The output message received from the agent.

        Returns:
            The output message to wrap in the Success or Failure outcome.
        """
        return result_message

    async def on_timeout(self) -> TaskOutputMessageModel:
        """Handle the case where the agent does not respond within the timeout.

        Override to return a substitute output message instead of failing. The default
        re-raises the TimeoutError so the task errors out.

        Returns:
            A substitute output message to report as the outcome.
        """
        # A bare raise re-raises the TimeoutError currently being handled in on_execute.
        raise

    @final
    async def on_launch(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        # Resolve the receive timeout from the original message before on_task can
        # replace it, matching the request_response_capability factory's ordering.
        self._recv_timeout = await self.resolve_timeout(task_message)
        return await self.on_task(task_message)

    @final
    async def on_execute(self) -> Success | Failure:
        try:
            result_message = await self.recv_from_agent(timeout=self._recv_timeout)
        except TimeoutError:
            # on_timeout re-raises by default; an override may return a substitute
            # result message to report instead.
            result_message = await self.on_timeout()
            return self._to_outcome(result_message)

        result_message = await self.on_result(result_message)
        if not isinstance(result_message, TaskOutputMessageModel):
            raise TypeError(
                "The `on_result` hook must return a `TaskOutputMessageModel`."
            )
        return self._to_outcome(result_message)

    @staticmethod
    def _to_outcome(result_message: TaskOutputMessageModel) -> Success | Failure:
        return (
            Success(result_message)
            if result_message.success
            else Failure(result_message)
        )


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
    """Build a request-response capability from callbacks (compatibility wrapper).

    This preserves the original factory interface but is now a thin adapter over
    RequestResponseCapability: it generates a subclass whose hook methods delegate to
    the supplied callbacks, threading a per-instance SimpleNamespace context through
    them exactly as before. Prefer subclassing RequestResponseCapability directly; this
    wrapper exists for backwards compatibility and for generating capabilities
    programmatically.

    See RequestResponseCapability for the meaning of each behavior. The callbacks map
    to hooks as follows: task_handler -> on_task, result_handler -> on_result,
    timeout_handler -> on_timeout, and timeout/resolve_timeout -> resolve_timeout.

    Returns:
        A new BaseAgentCapability subclass implementing the request-response behavior.
    """
    # Capture the callbacks under private names so the hook methods below can reference
    # them without shadowing this function's parameters.
    _timeout = timeout
    _resolve_timeout = resolve_timeout
    _task_handler = task_handler
    _result_handler = result_handler
    _timeout_handler = timeout_handler

    async def _resolve_timeout_hook(self, task_message):
        # Create the legacy context here (the first hook called) so it is shared across
        # every subsequent callback, mirroring the original factory.
        self._legacy_context = SimpleNamespace()
        context = self._legacy_context
        if _resolve_timeout:
            context.recv_timeout = _resolve_timeout(
                task_message=task_message, context=context
            )
        else:
            context.recv_timeout = _timeout
        return context.recv_timeout

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
            result_message = _result_handler(
                agent=self.agent,
                result_message=result_message,
                context=self._legacy_context,
            )
            if asyncio.iscoroutine(result_message):
                result_message = await result_message
        return result_message

    async def _on_timeout_hook(self):
        if _timeout_handler:
            result_message = _timeout_handler(
                agent=self.agent, context=self._legacy_context
            )
            if asyncio.iscoroutine(result_message):
                result_message = await result_message
            return result_message
        raise

    return type(
        "RequestResponseCapability",
        (RequestResponseCapability,),
        {
            "name": name,
            "description": description,
            "options": options,
            "authors": authors,
            "requires_admin": requires_admin,
            "mitre_attack_techniques": mitre_attack_techniques,
            "supported_oses": supported_oses,
            "validating_function": validating_function,
            "timeout": timeout,
            "resolve_timeout": _resolve_timeout_hook,
            "on_task": _on_task_hook,
            "on_result": _on_result_hook,
            "on_timeout": _on_timeout_hook,
        },
    )
