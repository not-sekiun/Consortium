from typing import final

from consortium.framework.agents.agent_capabilities.control_models import Finish
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
)
from consortium.framework.signal_exceptions import (
    AgentCapabilityExecutionError,
    AgentCapabilityLaunchError,
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

            async def on_response(self, task_output_message):
                task_output_message.message = task_output_message.message.strip()
                return task_output_message
        ```
    """

    timeout: int | float | None = None

    async def resolve_timeout(
        self,
        task_launch_message: TaskLaunchMessageModel,
        attempt: int,
    ) -> int | float | None:
        """Return the number of seconds to wait for the agent's response.

        Override to compute the timeout dynamically from the outgoing task message.
        The default returns the class-level timeout attribute. Re-armed on every
        receive attempt: attempt is 0 for the first wait and increments each time
        on_timeout asks to wait again, so a growing return value gives progressive
        backoff. task_launch_message is always the original, unmutated launch message,
        even across retries.

        Args:
            task_launch_message: The original task message sent to the agent.
            attempt: The 0-based number of consecutive receive timeouts so far.

        Returns:
            The receive timeout in seconds, or None to wait indefinitely.
        """
        return self.timeout

    async def on_request(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel:
        """Inspect or mutate the task message before it is sent to the agent.

        Override to enrich or replace the outgoing message. The default returns it
        unchanged. To deny the launch raise AgentCapabilityLaunchError; returning
        anything other than a TaskLaunchMessageModel is rejected as a launch error.

        Args:
            task_launch_message: The task message prepared for launch.

        Returns:
            The message to transmit.
        """
        return task_launch_message

    async def on_response(
        self,
        task_output_message: TaskOutputMessageModel,
    ) -> TaskOutputMessageModel:
        """Post-process the agent's response before it becomes the outcome.

        Override to reshape or annotate the response. The default returns it unchanged.

        Args:
            task_output_message: The output message received from the agent.

        Returns:
            The output message to wrap in the Success or Failure outcome.
        """
        return task_output_message

    async def on_timeout(self, attempt: int) -> Success | Failure | None:
        """Decide what to do when the agent does not respond within the timeout.

        The default raises an AgentCapabilityExecutionError, erroring the task so the
        timeout is visible in the task's event summary. Override to choose a different
        disposition:

            - Return None to wait again. This retries the receive: nothing is resent
              (retrying only re-waits, so no duplicate can reach the agent), and
              resolve_timeout is re-armed with an incremented attempt so the next wait
              can back off. Keep an eye on attempt to bound how long you keep waiting.
            - Return a Success or Failure to complete with that outcome.
            - Return the Finish sentinel to complete cleanly with no outcome. Note this
              is silent: the task completes normally with no timeout signal.
            - Raise (the default) to error the task.

        Args:
            attempt: The 0-based number of consecutive receive timeouts so far.

        Returns:
            None to wait again, a Success or Failure to report, or the Finish sentinel
            to complete with no outcome.
        """
        raise AgentCapabilityExecutionError(
            "Timed out waiting for the agent's response."
        )

    @final
    async def on_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel:
        # Capture the original, unmutated launch message so resolve_timeout always sees
        # it, even across retries, regardless of what on_request does next.
        self._launch_message = task_launch_message
        requested_message = await self.on_request(task_launch_message)
        # on_request must hand back a launch message; anything else (such as None)
        # denies the launch and is surfaced as an explicit launch error.
        if not isinstance(requested_message, TaskLaunchMessageModel):
            raise AgentCapabilityLaunchError(
                "`on_request` must return a `TaskLaunchMessageModel`, or raise "
                "`AgentCapabilityLaunchError` to deny the launch, but it returned "
                f"`{type(requested_message).__name__}`."
            )
        return requested_message

    @final
    async def on_execute(self) -> Success | Failure | None:
        # attempt counts consecutive receive timeouts; it re-arms resolve_timeout for
        # backoff and is only ever advanced by on_timeout asking to wait again.
        attempt = 0
        while True:
            recv_timeout = await self.resolve_timeout(
                task_launch_message=self._launch_message, attempt=attempt
            )
            try:
                response_message = await self.recv_from_agent(timeout=recv_timeout)
                break
            except TimeoutError:
                # on_timeout owns the disposition. Its default raises to error the task;
                # None waits again (retrying only re-waits: nothing is resent),
                # incrementing attempt for backoff; the Finish sentinel completes cleanly
                # with no outcome; a Success/Failure completes with that outcome.
                result = await self.on_timeout(attempt=attempt)
                if result is None:
                    attempt += 1
                    continue
                if result is Finish:
                    return None
                if isinstance(result, (Success, Failure)):
                    return result
                raise AgentCapabilityExecutionError(
                    "The `on_timeout` hook must return a `Success`, `Failure`, "
                    "`Finish`, or `None`."
                ) from None

        response_message = await self.on_response(response_message)
        if not isinstance(response_message, TaskOutputMessageModel):
            raise AgentCapabilityExecutionError(
                "The `on_response` hook must return a `TaskOutputMessageModel`."
            )
        return response_message.to_outcome()
