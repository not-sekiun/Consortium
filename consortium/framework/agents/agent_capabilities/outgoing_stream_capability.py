from typing import final

from consortium.framework.agents.agent_capabilities.control_models import Finish
from consortium.framework.agents.agent_message_models import (
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.framework.signal_exceptions import AgentCapabilityExecutionError


class OutgoingStreamCapability(BaseAgentCapability, abstract=True):
    # Optional idle deadline: the maximum number of seconds to wait for the single
    # final response (after half-close) before giving up. None (the default) waits
    # indefinitely, preserving the original forever-wait behaviour.
    idle_timeout: int | float | None = None

    async def resolve_idle_timeout(self, attempt: int) -> int | float | None:
        """Return the seconds to wait for the single final response before idling out.

        Override to compute the deadline dynamically. The default returns the
        class-level idle_timeout attribute. attempt is 0 for the first wait and
        increments each time on_idle_timeout asks to wait again, so a growing return
        value gives progressive backoff.

        Args:
            attempt: The 0-based number of consecutive idle timeouts while waiting for
                the final response.

        Returns:
            The idle timeout in seconds, or None to wait indefinitely.
        """
        return self.idle_timeout

    async def on_idle_timeout(self, attempt: int) -> Success | Failure | None:
        """Decide what to do when the final response never arrives in time.

        Called when, after half-closing, no final response arrives within the resolved
        idle_timeout. The default raises an AgentCapabilityExecutionError, erroring the
        task so the timeout is visible in the task's event summary. Override to choose a
        different disposition:

            - Return None to wait again for the final response. This retries the receive
              only: the whole stream was already sent and nothing is resent, and
              resolve_idle_timeout is re-armed with an incremented attempt for backoff.
            - Return a Success or Failure to end with that outcome.
            - Return the Finish sentinel to end cleanly with no outcome. Note this is
              silent: the task completes normally with no timeout signal.
            - Raise (the default) to error the task.

        Args:
            attempt: The 0-based number of consecutive idle timeouts so far.

        Returns:
            None to wait again, a Success or Failure to end and report it, or the Finish
            sentinel to end with no outcome.
        """
        raise AgentCapabilityExecutionError(
            "Timed out waiting for the agent's final response."
        )

    async def next_task_input(
        self,
    ) -> TaskInputMessageModel | Success | Failure:
        # Returns a TaskInputMessageModel to send, a Success/Failure to short-circuit
        # with that outcome, or the Finish sentinel to half-close (stop sending, then
        # await and process the single final response). Finish is a plain object()
        # sentinel and so cannot appear in the annotation until PEP 661 lands in 3.15.
        pass

    async def on_task_output(
        self, task_output_message: TaskOutputMessageModel
    ) -> Success | Failure | None:
        return task_output_message.to_outcome()

    async def on_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel:
        return task_launch_message

    @final
    async def on_execute(self) -> Success | Failure | None:
        while True:
            outgoing = await self.next_task_input()
            # A `Success`/`Failure` short-circuits: the developer has already decided
            # the result, so report it and skip the final response.
            if isinstance(outgoing, (Success, Failure)):
                return outgoing
            # A bare `Finish` is a half-close: stop sending, then await and process the
            # single final response from the agent.
            if outgoing is Finish:
                # attempt re-arms the deadline for backoff and only advances when
                # on_idle_timeout asks to wait again for the final response.
                attempt = 0
                while True:
                    idle_timeout = await self.resolve_idle_timeout(attempt=attempt)
                    try:
                        final_response = await self.recv_from_agent(
                            timeout=idle_timeout
                        )
                        break
                    except TimeoutError:
                        # on_idle_timeout owns the disposition. Its default raises to
                        # error the task. None waits again (nothing is resent),
                        # incrementing attempt for backoff; the Finish sentinel ends
                        # cleanly with no outcome; a Success/Failure ends with that
                        # outcome.
                        result = await self.on_idle_timeout(attempt=attempt)
                        if result is None:
                            attempt += 1
                            continue
                        if result is Finish:
                            return None
                        if isinstance(result, (Success, Failure)):
                            return result
                        raise AgentCapabilityExecutionError(
                            "`on_idle_timeout` must return a `Success`, `Failure`, "
                            "`Finish`, or `None` but instead returned value of type "
                            f"{type(result).__name__}"
                        ) from None
                return await self.on_task_output(task_output_message=final_response)
            if not isinstance(outgoing, TaskInputMessageModel):
                raise AgentCapabilityExecutionError(
                    "`next_task_input` must return a `TaskInputMessageModel`, "
                    "`Success`, `Failure`, or `Finish` but instead returned value of "
                    f"type {type(outgoing).__name__}"
                )
            await self.send_to_agent(task_message=outgoing)
