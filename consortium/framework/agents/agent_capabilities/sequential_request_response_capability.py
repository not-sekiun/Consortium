from typing import final

from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.base_agent_capability import BaseAgentCapability


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
