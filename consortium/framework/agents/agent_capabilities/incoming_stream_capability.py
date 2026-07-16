from typing import final

from consortium.framework.agents.agent_capabilities.control_models import Finish
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.framework.signal_exceptions import AgentCapabilityExecutionError


class IncomingStreamCapability(BaseAgentCapability, abstract=True):
    # Optional idle deadline: the maximum number of seconds to wait for the next
    # streamed response before the stream is treated as idle. None (the default) waits
    # indefinitely, preserving the original forever-wait behaviour.
    idle_timeout: int | float | None = None

    async def resolve_idle_timeout(
        self, index: int, attempt: int
    ) -> int | float | None:
        """Return the seconds to wait for the next response before idling out.

        Override to compute the idle deadline dynamically. The default returns the
        class-level idle_timeout attribute. The deadline is re-armed for every response,
        so it bounds the gap between responses, not the whole stream. attempt is 0 for
        the first wait and increments each time on_idle_timeout asks to wait again, so a
        growing return value gives progressive backoff; it resets to 0 once a response
        arrives.

        Args:
            index: The 0-based count of responses received so far this execution.
            attempt: The 0-based number of consecutive idle timeouts while waiting for
                the next response.

        Returns:
            The idle timeout in seconds, or None to wait indefinitely.
        """
        return self.idle_timeout

    async def on_idle_timeout(
        self, index: int, attempt: int
    ) -> Success | Failure | None:
        """Decide what to do when the stream goes idle (no response in time).

        Called when no response arrives within the resolved idle_timeout. The default
        raises an AgentCapabilityExecutionError, erroring the task so the timeout is
        visible in the task's event summary. Override to choose a different disposition:

            - Return None to wait again for the next response. This retries the receive
              only (nothing is ever resent), and resolve_idle_timeout is re-armed with
              an incremented attempt so the next wait can back off. Watch attempt to
              bound how long you keep waiting on a silent agent.
            - Return a Success or Failure to end the stream with that outcome.
            - Return the Finish sentinel to end the stream cleanly with no outcome. Note
              this is silent: the task completes normally with no timeout signal.
            - Raise (the default) to error the task.

        Args:
            index: The 0-based count of responses received before the stream idled out.
            attempt: The 0-based number of consecutive idle timeouts so far.

        Returns:
            None to wait again, a Success or Failure to end and report that outcome, or
            the Finish sentinel to end with no outcome.
        """
        raise AgentCapabilityExecutionError(
            "The incoming stream timed out waiting for the next response from the agent."
        )

    async def on_task_output(
        self, index: int, task_output_message: TaskOutputMessageModel
    ) -> Success | Failure | None:
        pass

    async def on_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel:
        return task_launch_message

    @final
    async def on_execute(self) -> Success | Failure | None:
        index = 0
        # attempt counts consecutive idle timeouts while waiting for the next response;
        # it re-arms the deadline for backoff and resets once a response arrives.
        attempt = 0
        while True:
            idle_timeout = await self.resolve_idle_timeout(index=index, attempt=attempt)
            try:
                task_output_message = await self.recv_from_agent(timeout=idle_timeout)
            except TimeoutError:
                # on_idle_timeout owns the disposition. Its default raises to error the
                # task. None waits again (retrying only re-waits, never a resend),
                # incrementing attempt for backoff; the Finish sentinel ends the stream
                # cleanly; a Success/Failure ends it with that outcome.
                result = await self.on_idle_timeout(index=index, attempt=attempt)
                if result is None:
                    attempt += 1
                    continue
                if result is Finish:
                    return None
                if isinstance(result, (Success, Failure)):
                    return result
                raise AgentCapabilityExecutionError(
                    "`on_idle_timeout` must return a `Success`, `Failure`, `Finish`, "
                    f"or `None` but instead returned value of type "
                    f"{type(result).__name__}"
                ) from None
            # A response arrived; reset the consecutive-timeout counter for the next wait.
            attempt = 0
            result = await self.on_task_output(
                index=index, task_output_message=task_output_message
            )
            # A `Success`/`Failure` stops the stream and becomes the task result; the
            # `Finish` sentinel stops with no outcome; `None` continues the loop to await
            # the next response.
            if result is Finish:
                return None
            if isinstance(result, (Success, Failure)):
                return result
            if result is not None:
                raise AgentCapabilityExecutionError(
                    "`on_task_output` must return a `Success`, `Failure`, "
                    "`Finish`, or `None` but instead returned value of type "
                    f"{type(result).__name__}"
                )
            index += 1
