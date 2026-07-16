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


class LockStepStreamCapability(BaseAgentCapability, abstract=True):
    """Template base class for a turn-based Launch (Input Output)* stream.

    This is the lock-step member of the stream family: input and output are
    streamed one round at a time, each input waiting on the response that
    preceded it. The task launch message is a one-off prologue: it is prepared by
    on_prepare, sent once by execute, and never re-enters the exchange loop. Every
    subsequent outgoing message is a TaskInputMessageModel built by next_task_input
    from the response that preceded it.

    Rounds are numbered by the exchange they belong to: round 0 awaits the response
    to the launch message, and round n (n >= 1) awaits the response to the nth input
    message. on_task_output decides after each response whether to continue;
    continuing past the iterations cap simply ends the loop with the last response
    as the outcome.

    Timeouts extend patience, they never resend: when a round's response does not
    arrive in time, on_timeout is consulted. Returning None waits again for that same
    round's response (retrying only re-waits, so no duplicate can reach an agent that
    never opted into de-duplicating one), and the framework never advances the round on
    a timeout. That is deliberate: the strict input/output pairing that defines lock
    step only holds while send and receive stay aligned, so the loop can wait longer for
    the pending response but can never skip ahead to the next input without a response to
    build it from. By default on_timeout raises, erroring the task so the timeout is
    visible in the event summary; override it to wait again (return None), stop cleanly
    (return the Finish sentinel), or report a Success/Failure.

    Attributes:
        timeout (int | float | None): Default number of seconds to wait for each
            round's response. None waits indefinitely. Override resolve_timeout for a
            per-round value.
        iterations (int | None): Maximum number of input messages to send after the
            launch. 0 degenerates to plain request-response (launch, first response,
            done). None runs the loop until on_task_output stops it. Override
            resolve_iterations for a value computed from the launch message.
    """

    timeout: int | float | None = None
    iterations: int | None = None

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
            The maximum number of input messages, or None to loop until
            on_task_output stops it.
        """
        return self.iterations

    async def resolve_timeout(
        self,
        index: int,
        current_task_message: TaskLaunchMessageModel | TaskInputMessageModel,
        attempt: int,
    ) -> int | float | None:
        """Return the number of seconds to wait for the current round's response.

        Override to compute the timeout dynamically per round. The default returns
        the class-level timeout attribute. Re-armed on every receive attempt within a
        round: attempt is 0 for the first wait and increments each time on_timeout asks
        to wait again, so a growing return value gives progressive backoff. attempt
        resets to 0 when a new round begins.

        Args:
            index: The 0-based round index (0 = the launch exchange, n = the nth
                input exchange).
            current_task_message: The message whose response is being awaited.
            attempt: The 0-based number of consecutive timeouts on this round's
                response so far.

        Returns:
            The receive timeout in seconds, or None to wait indefinitely.
        """
        return self.timeout

    async def on_prepare(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel:
        """Inspect or mutate the launch message before it is sent.

        Override to prepare the one-off launch message. The default returns it
        unchanged. This is the only hook that handles a TaskLaunchMessageModel and
        the only place the launch can be denied. To deny the launch raise
        AgentCapabilityLaunchError; returning anything other than a
        TaskLaunchMessageModel is rejected as a launch error.

        Args:
            task_launch_message: The task launch message about to be sent.

        Returns:
            The launch message to transmit.
        """
        return task_launch_message

    async def next_task_input(
        self,
        index: int,
        task_output_message: TaskOutputMessageModel,
    ) -> TaskInputMessageModel:
        """Build the next input message from the response that preceded it.

        Override to construct each follow-up message; this is the core hook of the
        lock-step exchange. The default constructs a bare TaskInputMessageModel, which
        is only useful when the model requires no fields. Called once per continued
        round; never called for the launch or for resends.

        Args:
            index: The 0-based round index the new input message belongs to (>= 1).
            task_output_message: The response received in the previous round.

        Returns:
            The fully populated input message to transmit.
        """
        return self.create_task_input_message()

    async def on_task_output(
        self,
        index: int,
        task_output_message: TaskOutputMessageModel,
    ) -> Success | Failure | None:
        """Process a received response and decide whether to continue the loop.

        Override to inspect each reply. Return None to continue: the received response
        is passed to next_task_input to build the next input. Return a
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
        attempt: int,
    ) -> Success | Failure | None:
        """Decide what to do for a round whose response timed out.

        The default raises an AgentCapabilityExecutionError, erroring the task so the
        timeout is visible in the task's event summary. Override to choose a different
        disposition:

            - Return None to wait again for this round's response. This retries the
              receive only: the framework never resends and never advances the round,
              so the lock-step input/output pairing is preserved. resolve_timeout is
              re-armed with an incremented attempt so the next wait can back off; watch
              attempt to bound how long you keep waiting.
            - Return a Success or Failure to stop the loop and report that outcome.
            - Return the Finish sentinel to end the loop cleanly with no outcome. Note
              this is silent: the task completes normally with no timeout signal.
            - Raise (the default) to error the task.

        There is deliberately no "skip this round" option: advancing to the next input
        would need a response to build it from, and it would also duplicate or desync
        the exchange. If the pairing is broken you can only keep waiting or stop.

        Args:
            index: The 0-based round index that went unanswered.
            current_task_message: The message (launch or input) whose response has not
                arrived.
            attempt: The 0-based number of consecutive timeouts on this round so far.

        Returns:
            None to wait again, a Success or Failure to stop and report it, or the
            Finish sentinel to end with no outcome.
        """
        raise AgentCapabilityExecutionError(
            f"Timed out waiting for the agent's response in round {index}."
        )

    async def on_completed(
        self,
        index: int,
        outcome: Success | Failure | None,
        stopped_early: bool,
    ) -> None:
        """Observe the loop's final result before it is returned.

        Override to react to the end of the exchange. The default does nothing.
        Called on every normal termination: on_task_output stopping the loop, the
        iterations cap being exhausted, or on_timeout ending it with an outcome or a
        clean Finish. Not called when a hook ends the loop by raising.

        Args:
            index: The 0-based index of the final round.
            outcome: The final outcome about to be returned to the framework, or None
                when the loop stopped with no outcome (the Finish sentinel).
            stopped_early: True when on_task_output or on_timeout ended the loop before
                the iterations cap was reached (always True when the cap is None);
                False when the loop stopped because the cap was exhausted.
        """
        return None

    @final
    async def on_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel:
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
        prepared_message = await self.on_prepare(
            task_launch_message=task_launch_message
        )
        # on_prepare must hand back a launch message; anything else (such as
        # None) denies the launch and is surfaced as an explicit launch error.
        if not isinstance(prepared_message, TaskLaunchMessageModel):
            raise AgentCapabilityLaunchError(
                "`on_prepare` must return a `TaskLaunchMessageModel`, or raise "
                "`AgentCapabilityLaunchError` to deny the launch, but it returned "
                f"`{type(prepared_message).__name__}`."
            )
        return prepared_message

    @final
    async def on_execute(self) -> Success | Failure | None:
        current_task_message: TaskLaunchMessageModel | TaskInputMessageModel = (
            self.task_launch_message
        )
        index = 0

        while True:
            # Inner receive loop for the current round. attempt re-arms the timeout for
            # backoff and only ever advances when on_timeout asks to wait again; it is
            # reset to 0 for each new round because current_task_message is reassigned.
            attempt = 0
            while True:
                recv_timeout = await self.resolve_timeout(
                    index=index,
                    current_task_message=current_task_message,
                    attempt=attempt,
                )
                try:
                    received_message = await self.recv_from_agent(timeout=recv_timeout)
                    break
                except TimeoutError:
                    # on_timeout owns the disposition. Its default raises to error the
                    # task. None waits again for THIS round's response: the framework
                    # never resends and never advances the round, so the strict lock-step
                    # pairing holds; attempt increments for backoff. The Finish sentinel
                    # ends the loop cleanly; a Success/Failure ends it with that outcome.
                    outcome = await self.on_timeout(
                        index=index,
                        current_task_message=current_task_message,
                        attempt=attempt,
                    )
                    if outcome is None:
                        attempt += 1
                        continue
                    if outcome is Finish:
                        await self.on_completed(
                            index=index, outcome=None, stopped_early=True
                        )
                        return None
                    if isinstance(outcome, (Success, Failure)):
                        await self.on_completed(
                            index=index, outcome=outcome, stopped_early=True
                        )
                        return outcome
                    raise AgentCapabilityExecutionError(
                        "`on_timeout` must return a `Success`, `Failure`, `Finish`, or "
                        f"`None` but instead returned value of type "
                        f"{type(outcome).__name__}"
                    ) from None

            result = await self.on_task_output(
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
                    "`on_task_output` must return a `Success`, `Failure`, `Finish`, or "
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
            current_task_message = await self.next_task_input(
                index=index, task_output_message=received_message
            )
            await self.send_to_agent(task_message=current_task_message)
