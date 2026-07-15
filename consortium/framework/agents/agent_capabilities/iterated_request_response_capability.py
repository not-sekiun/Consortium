from typing import final

from consortium.framework.agents.agent_capabilities.control_models import Finish
from consortium.framework.agents.agent_message_models import (
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.framework.signal_exceptions import (
    AgentCapabilityExecutionError,
    AgentCapabilityLaunchError,
)


class IteratedRequestResponseCapability(BaseAgentCapability, abstract=True):
    """Template base class for capabilities following a Launch Output (Input Output)* protocol.

    The task launch message is a one-off prologue: it is prepared by prepare_launch,
    sent once by execute, and never re-enters the exchange loop. Every subsequent
    outgoing message is a TaskInputMessageModel built by create_input_message from
    the response that preceded it.

    Rounds are numbered by the exchange they belong to: round 0 awaits the response
    to the launch message, and round n (n >= 1) awaits the response to the nth input
    message. on_response decides after each response whether to continue; continuing
    past the iterations cap simply ends the loop with the last response as the
    outcome.

    Timeouts are handled by a retry policy, not by the exchange loop: a missed
    response is resent verbatim up to max_resends times per round (resolve_max_resends
    for a per-round value). Only when the retry budget is exhausted is on_timeout
    consulted for a final disposition -- there is no way to "continue" past an
    exhausted round, because no response exists to build the next input from.

    Attributes:
        timeout (int | float | None): Default number of seconds to wait for each
            response attempt. None waits indefinitely. Override resolve_timeout for a
            per-round value.
        iterations (int | None): Maximum number of input messages to send after the
            launch. 0 degenerates to plain request-response (launch, first response,
            done). None runs the loop until on_response stops it. Override
            resolve_iterations for a value computed from the launch message.
        max_resends (int): Number of verbatim resends allowed per round when a
            response times out. 0 (the default) disables retries. Override
            resolve_max_resends for a per-round value.
    """

    timeout: int | float | None = None
    iterations: int | None = None
    max_resends: int = 0

    # Resolved input-message cap, populated by on_launch before the loop starts.
    _max_iterations: int | None = None

    async def resolve_iterations(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> int | None:
        """Return the maximum number of input messages to send after the launch.

        Override to compute the cap dynamically from the launch message. The default
        returns the class-level iterations attribute. The value is validated at
        launch: it must be None or at least 0. The launch message is not counted; 0
        means launch-only request-response.

        Args:
            task_launch_message: The initial task message about to be launched.

        Returns:
            The maximum number of input messages, or None to loop until on_response
            stops it.
        """
        return self.iterations

    async def resolve_timeout(
        self,
        index: int,
        current_task_message: TaskLaunchMessageModel | TaskInputMessageModel,
    ) -> int | float | None:
        """Return the number of seconds to wait for the current round's response.

        Override to compute the timeout dynamically per round. The default returns
        the class-level timeout attribute. Resend attempts within a round reuse the
        round's resolved timeout.

        Args:
            index: The 0-based round index (0 = the launch exchange, n = the nth
                input exchange).
            current_task_message: The message whose response is being awaited.

        Returns:
            The receive timeout in seconds, or None to wait indefinitely.
        """
        return self.timeout

    async def resolve_max_resends(
        self,
        index: int,
        current_task_message: TaskLaunchMessageModel | TaskInputMessageModel,
    ) -> int:
        """Return the number of verbatim resends permitted for this round.

        Override to compute the retry budget dynamically per round. The default
        returns the class-level max_resends attribute. A resend repeats the round's
        outgoing message unchanged; it does not advance the round index and does not
        count against the iterations cap.

        Args:
            index: The 0-based round index.
            current_task_message: The message that would be resent.

        Returns:
            The number of resend attempts allowed after the initial send (0 disables
            retries for this round).
        """
        return self.max_resends

    async def on_prepare_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        """Inspect, mutate, or cancel the launch message before it is sent.

        Override to prepare the one-off launch message. The default returns it
        unchanged. This is the only hook that handles a TaskLaunchMessageModel and
        the only place cancellation is possible.

        Args:
            task_launch_message: The task launch message about to be sent.

        Returns:
            The launch message to transmit, or None to cancel the launch (execute
            returns None and the loop never starts).
        """
        return task_launch_message

    async def on_create_next_input_message(
        self,
        index: int,
        task_output_message: TaskOutputMessageModel,
    ) -> TaskInputMessageModel:
        """Build the next input message from the response that preceded it.

        Override to construct each follow-up message; this is the core hook of the
        iterated exchange. The default constructs a bare TaskInputMessageModel, which
        is only useful when the model requires no fields. Called once per continued
        round; never called for the launch or for resends.

        Args:
            index: The 0-based round index the new input message belongs to (>= 1).
            task_output_message: The response received in the previous round.

        Returns:
            The fully populated input message to transmit.
        """
        return self.create_task_input_message()

    async def on_response(
        self,
        index: int,
        task_output_message: TaskOutputMessageModel,
    ) -> Success | Failure | None:
        """Process a received response and decide whether to continue the loop.

        Override to inspect each reply. Return None to continue: the received response
        is passed to on_create_next_input_message to build the next input. Return a
        Success or Failure to stop and report that outcome, or the Finish sentinel to
        stop with no outcome (the capability returns None). The default stops after the
        first response, reporting the received message as the outcome.

        When you continue but the iterations cap is then reached, the loop stops on
        its own and reports the last received response as the outcome (see
        resolve_iterations).

        Args:
            index: The 0-based round index (0 = response to the launch, n = response
                to the nth input message).
            task_output_message: The output message received this round.

        Returns:
            None to continue, a Success or Failure to stop and report it, or the Finish
            sentinel to stop with no outcome.
        """
        return task_output_message.to_outcome()

    async def on_timeout(
        self,
        index: int,
        current_task_message: TaskLaunchMessageModel | TaskInputMessageModel,
    ) -> TaskOutputMessageModel | None:
        """Provide a final disposition after a round's retry budget is exhausted.

        Override to substitute an outcome for an unanswered round. The default
        returns None, which propagates the pending TimeoutError. There is no option
        to continue: with no response in hand there is nothing to build the next
        input message from. Configure resends via max_resends / resolve_max_resends
        instead.

        Args:
            index: The 0-based round index that went unanswered.
            current_task_message: The message (launch or input) whose response never
                arrived, including after any resends.

        Returns:
            A message to report as the final outcome (on_completed is invoked and the
            message is returned), or None to re-raise the TimeoutError.
        """
        return None

    async def on_completed(
        self,
        index: int,
        outcome: Success | Failure | None,
        stopped_early: bool,
    ) -> None:
        """Observe the loop's final result before it is returned.

        Override to react to the end of the exchange. The default does nothing.
        Called on every normal termination: on_response stopping the loop, the
        iterations cap being exhausted, or on_timeout substituting an outcome. Not
        called when the loop ends by raising a propagated TimeoutError.

        Args:
            index: The 0-based index of the final round.
            outcome: The final outcome about to be returned to the framework, or None
                when on_response stopped with no outcome (the Finish sentinel).
            stopped_early: True when on_response or on_timeout ended the loop before
                the iterations cap was reached (always True when the cap is None);
                False when the loop stopped because the cap was exhausted.
        """
        return None

    @final
    async def on_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        max_iterations = await self.resolve_iterations(
            task_launch_message=task_launch_message
        )
        if max_iterations is not None and max_iterations < 0:
            raise AgentCapabilityLaunchError(
                f"Iterations must be None or at least 0, got {max_iterations}. The "
                "launch message is not counted; 0 means launch-only "
                "request-response."
            )
        self._max_iterations = max_iterations
        return await self.on_prepare_launch(task_launch_message=task_launch_message)

    @final
    async def on_execute(self) -> Success | Failure | None:
        current_task_message: TaskLaunchMessageModel | TaskInputMessageModel = (
            self.task_launch_message
        )
        index = 0

        while True:
            recv_timeout = await self.resolve_timeout(
                index=index, current_task_message=current_task_message
            )
            resends_left = await self.resolve_max_resends(
                index=index, current_task_message=current_task_message
            )

            # Await the round's response, retrying verbatim while budget remains.
            while True:
                try:
                    received_message = await self.recv_from_agent(timeout=recv_timeout)
                except TimeoutError:
                    if resends_left > 0:
                        resends_left -= 1
                        await self.send_to_agent(task_message=current_task_message)
                        continue
                    result_message = await self.on_timeout(
                        index=index, current_task_message=current_task_message
                    )
                    if result_message is None:
                        raise  # Nothing to report, so propagate the timeout.
                    outcome = result_message.to_outcome()
                    await self.on_completed(
                        index=index, outcome=outcome, stopped_early=True
                    )
                    return outcome
                else:
                    break

            result = await self.on_response(
                index=index, task_output_message=received_message
            )
            # A `Success`/`Failure` stops the loop and is reported; the `Finish` sentinel
            # stops with no outcome; `None` continues, using this round's response to
            # build the next input message.
            if result is Finish:
                await self.on_completed(index=index, outcome=None, stopped_early=True)
                return None
            if isinstance(result, (Success, Failure)):
                await self.on_completed(index=index, outcome=result, stopped_early=True)
                return result
            if result is not None:
                raise AgentCapabilityExecutionError(
                    "`on_response` must return a `Success`, `Failure`, `Finish`, or "
                    f"`None` but instead returned value of type {type(result).__name__}"
                )

            # index counts completed exchanges, which equals the number of input
            # messages sent so far; stop once the cap forbids another input. With no
            # explicit Finish, this round's response is reported as the outcome.
            if self._max_iterations is not None and index >= self._max_iterations:
                outcome = received_message.to_outcome()
                await self.on_completed(
                    index=index, outcome=outcome, stopped_early=False
                )
                return outcome

            index += 1
            current_task_message = await self.on_create_next_input_message(
                index=index, task_output_message=received_message
            )
            await self.send_to_agent(task_message=current_task_message)
