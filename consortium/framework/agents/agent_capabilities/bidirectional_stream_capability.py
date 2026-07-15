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

    Two directions run concurrently: on_handle_outgoing_message produces messages to
    send, while on_handle_incoming_message consumes messages as they arrive. Streamed
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
    other) is deliberately not offered yet: without receive timeouts it is a silent-hang
    footgun with no genuine use case that half-close does not already cover.
    """

    async def _outgoing_message_task_handler(self) -> None:
        while True:
            outgoing_message_or_finish = await self.on_handle_outgoing_message()
            if isinstance(outgoing_message_or_finish, TaskInputMessageModel):
                await self.send_to_agent(task_message=outgoing_message_or_finish)
            elif outgoing_message_or_finish is Finish:
                # A half-close: stop sending. The incoming stream keeps running and owns
                # the task outcome.
                return
            else:
                raise AgentCapabilityExecutionError(
                    "`on_handle_outgoing_message` must return a "
                    "`TaskInputMessageModel` or `Finish` but instead returned value of "
                    f"type {type(outgoing_message_or_finish).__name__}"
                )

    async def _incoming_message_task_handler(self) -> Success | Failure | None:
        index = 0
        while True:
            task_output_message = await self.recv_from_agent()
            result = await self.on_handle_incoming_message(
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
                    "`on_handle_incoming_message` must return a `Success`, `Failure`, "
                    "`Finish`, or `None` but instead returned value of type "
                    f"{type(result).__name__}"
                )
            index += 1

    async def on_handle_outgoing_message(
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

    async def on_handle_incoming_message(
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
    ) -> TaskLaunchMessageModel | None:
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
