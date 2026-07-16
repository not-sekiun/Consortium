import asyncio
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


class BidirectionalStreamCapability(BaseAgentCapability, abstract=True):
    """Template base class for a full-duplex exchange with the agent.

    Two directions run concurrently: next_task_input produces messages to
    send, while on_task_output consumes messages as they arrive. Streamed
    output is reported through the emit_* events; think of it as a pseudo virtual TTY
    where the launch message initiates, the outgoing side is the input channel, and the
    emitted events are the output channel.

    Termination follows the gRPC half-close model, which keeps the common case (command
    streaming: start / stop / redo with output streaming back) simple to write:

        - The outgoing handler returning the Finish sentinel is a half-close: it stops
          the send loop but the incoming stream keeps flowing. The send side never
          produces the result; once you have decided you are done sending, you should not
          send anything more, but the agent may still have messages for you.
        - The incoming handler ends the exchange by returning a Success or Failure (which
          becomes the task result) or the Finish sentinel (which completes the task
          normally, having reported everything via emit_*). The agent has decided it is
          done, so nothing on our side should keep it open: the send loop is cancelled.
        - Either handler raising aborts the whole exchange and errors the task.

    Full independence between the two channels (both must finish, neither cancels the
    other) is deliberately not offered: there is no genuine use case that the half-close
    model does not already cover. An optional idle_timeout bounds how long the incoming
    side waits for the next message; on_idle_timeout then decides whether to wait again
    (backing off), end the exchange cleanly, or report an outcome, so a silent agent need
    not hang forever.
    """

    # Optional idle deadline for the incoming side: the maximum number of seconds to
    # wait for the next message from the agent before the exchange is treated as idle.
    # None (the default) waits indefinitely, preserving the original behaviour.
    idle_timeout: int | float | None = None

    async def resolve_idle_timeout(
        self, index: int, attempt: int
    ) -> int | float | None:
        """Return the seconds to wait for the next incoming message before idling out.

        Override to compute the idle deadline dynamically. The default returns the
        class-level idle_timeout attribute. The deadline is re-armed for every incoming
        message, so it bounds the gap between messages, not the whole exchange. attempt
        is 0 for the first wait and increments each time on_idle_timeout asks to wait
        again, so a growing return value gives progressive backoff; it resets to 0 once a
        message arrives.

        Args:
            index: The 0-based count of messages received from the agent so far.
            attempt: The 0-based number of consecutive idle timeouts while waiting for
                the next message.

        Returns:
            The idle timeout in seconds, or None to wait indefinitely.
        """
        return self.idle_timeout

    async def on_idle_timeout(
        self, index: int, attempt: int
    ) -> Success | Failure | None:
        """Decide what to do when the incoming side goes idle (no message in time).

        Called when no message arrives within the resolved idle_timeout. The default
        raises an AgentCapabilityExecutionError, erroring the task so the timeout is
        visible in the task's event summary. Override to choose a different disposition:

            - Return None to wait again for the next message. This retries the receive
              only (nothing is ever resent), and resolve_idle_timeout is re-armed with an
              incremented attempt so the next wait can back off.
            - Return a Success or Failure to end the exchange with that outcome.
            - Return the Finish sentinel to end the exchange cleanly with no outcome
              (under the half-close model this also cancels the send loop). Note this is
              silent: the task completes normally with no timeout signal.
            - Raise (the default) to error the task.

        Args:
            index: The 0-based count of messages received before the side idled out.
            attempt: The 0-based number of consecutive idle timeouts so far.

        Returns:
            None to wait again, a Success or Failure to end and report that outcome, or
            the Finish sentinel to end the exchange with no outcome.
        """
        raise AgentCapabilityExecutionError(
            "The incoming stream timed out waiting for the next message from the agent."
        )

    async def _outgoing_message_task_handler(self) -> None:
        while True:
            outgoing_message_or_finish = await self.next_task_input()
            if isinstance(outgoing_message_or_finish, TaskInputMessageModel):
                await self.send_to_agent(task_message=outgoing_message_or_finish)
            elif outgoing_message_or_finish is Finish:
                # A half-close: stop sending. The incoming stream keeps running and owns
                # the task outcome.
                return
            else:
                raise AgentCapabilityExecutionError(
                    "`next_task_input` must return a "
                    "`TaskInputMessageModel` or `Finish` but instead returned value of "
                    f"type {type(outgoing_message_or_finish).__name__}"
                )

    async def _incoming_message_task_handler(self) -> Success | Failure | None:
        index = 0
        # attempt counts consecutive idle timeouts while waiting for the next message;
        # it re-arms the deadline for backoff and resets once a message arrives.
        attempt = 0
        while True:
            idle_timeout = await self.resolve_idle_timeout(index=index, attempt=attempt)
            try:
                task_output_message = await self.recv_from_agent(timeout=idle_timeout)
            except TimeoutError:
                # on_idle_timeout owns the disposition. Its default raises to error the
                # task. None waits again (retrying only re-waits, never a resend),
                # incrementing attempt for backoff; the Finish sentinel ends the exchange
                # cleanly, which under the half-close model cancels the send loop; a
                # Success/Failure ends it with that outcome.
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
            # A message arrived; reset the consecutive-timeout counter for the next wait.
            attempt = 0
            result = await self.on_task_output(
                index=index, task_output_message=task_output_message
            )
            # A `Success`/`Failure` ends the exchange and becomes the task result; the
            # `Finish` sentinel ends it with no outcome; `None` continues the loop to
            # await the next message.
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

    async def next_task_input(
        self,
    ) -> TaskInputMessageModel:
        """Produce the next message to send to the agent, or half-close the send side.

        Called repeatedly to drive the outgoing (input) channel. Override to build each
        message. Return a TaskInputMessageModel to send it, or the Finish sentinel to
        half-close: stop sending while the incoming stream keeps flowing. The incoming
        handler owns the task result.

        Returns:
            The next message to send, or Finish to stop sending.
        """

    async def on_task_output(
        self, index: int, task_output_message: TaskOutputMessageModel
    ) -> Success | Failure | None:
        """Consume a message from the agent and decide whether the exchange is over.

        Called for each message the agent sends. Override to process it, typically
        reporting streamed output via the emit_* events. Return None to keep receiving,
        a Success or Failure to end the exchange and report that outcome, or the Finish
        sentinel to end the exchange with no outcome. Ending the exchange cancels the
        send loop; the returned outcome (or None for Finish) becomes the task result.

        Args:
            index: The 0-based count of messages received from the agent this execution
                (0 for the first message, incremented once per continued round).
            task_output_message: The message just received from the agent.

        Returns:
            None to continue receiving, a Success or Failure to end and report it, or
            the Finish sentinel to end with no outcome.
        """

    async def on_launch(
        self, task_launch_message: TaskLaunchMessageModel
    ) -> TaskLaunchMessageModel:
        return task_launch_message

    @final
    async def on_execute(self) -> Success | Failure | None:
        # The two directions run concurrently. Under the half-close model the incoming
        # stream owns termination: the outgoing handler returning is only a half-close,
        # so we never cancel the receive loop just because we finished sending, but we
        # do cancel the send loop once the agent ends the incoming stream.
        outgoing_task = asyncio.create_task(self._outgoing_message_task_handler())
        incoming_task = asyncio.create_task(self._incoming_message_task_handler())
        try:
            done, _ = await asyncio.wait(
                {outgoing_task, incoming_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            # If only the outgoing side finished and it half-closed cleanly (no error),
            # keep waiting for the agent to close the incoming stream. asyncio.wait is
            # used rather than awaiting the task directly so a later incoming error is
            # left stored on the task and surfaced uniformly below.
            if incoming_task not in done and outgoing_task.exception() is None:
                await asyncio.wait({incoming_task})
        finally:
            # Tear down whatever is still running. A cleanly half-closed outgoing task
            # and a finished incoming task are already done, so cancel() is a no-op for
            # them; the incoming task is only actually cancelled when the outgoing side
            # aborted with an error.
            outgoing_task.cancel()
            incoming_task.cancel()
            await asyncio.gather(outgoing_task, incoming_task, return_exceptions=True)

        # An error from the send side aborts the exchange and errors the task. Otherwise
        # the incoming stream owns the terminal outcome (or raised, which result()
        # re-surfaces); returning None completes the task normally.
        if not outgoing_task.cancelled() and outgoing_task.exception() is not None:
            raise outgoing_task.exception()
        return incoming_task.result()
