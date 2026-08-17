from pydantic import JsonValue

from consortium.framework._core.framework_exceptions.base_framework_exception import (
    BaseFrameworkError,
)


class AgentMessagesFrameworkError(BaseFrameworkError):
    """Base exception for all errors that occur within the agent messages framework."""

    code = "AGENT_MESSAGES_FRAMEWORK_ERROR"


class AgentIncomingMessageRejectedError(AgentMessagesFrameworkError):
    """Base exception for every reason the framework refuses a message from an agent.

    The one type a listener catches. A listener hands the framework whatever an agent
    sent and gets back either something to send, nothing to send, or this: it answers
    its own uniform rejection for the transport it speaks (an HTTP 401, a closed
    socket) without branching on why, because telling an unauthenticated caller which
    of these it tripped tells it how to probe for the others.

    The subtype and its `code` exist for the server's side of that: logs, events, and
    the API can tell a garbled body from an unknown task, and `detail` carries the
    identifiers involved. None of that is for the agent, so nothing in `message` or
    `detail` should reach the wire.

    Catch this to reject; match on the subtype or `code` to explain.
    """

    code = "AGENT_INCOMING_MESSAGE_REJECTED_ERROR"

    def __init__(
        self,
        error_message: str,
        detail: dict[str, JsonValue] | None = None,
    ):
        super().__init__(
            message=f"Rejected an incoming agent message. {error_message}",
            detail=detail,
        )


class MalformedAgentMessageError(AgentIncomingMessageRejectedError):
    """Raised when an incoming message cannot be decoded into a JSON object at all.

    The failure before any schema is consulted: bytes that are not valid JSON, or JSON
    that is not an object, so there is no `type` field to discriminate on and nothing to
    say about which message it failed to be.
    """

    code = "MALFORMED_AGENT_MESSAGE_ERROR"

    def __init__(self, error_message: str = "The message could not be decoded."):
        super().__init__(error_message=error_message)


class InvalidAgentMessageError(AgentIncomingMessageRejectedError):
    """Raised when a decoded incoming message does not satisfy the message schema.

    Covers both halves of that validation: a `type` that names no known message, and a
    message whose `type` is known but whose fields are missing, mistyped, or extra. The
    open `arguments` and `data` dictionaries are never a cause, since the framework does
    not open them.
    """

    code = "INVALID_AGENT_MESSAGE_ERROR"

    def __init__(
        self,
        error_message: str,
        detail: dict[str, JsonValue] | None = None,
    ):
        super().__init__(
            error_message=(
                f"The message did not match the schema of any known message type. "
                f"{error_message}"
            ),
            detail=detail,
        )


class UnidentifiedAgentError(AgentIncomingMessageRejectedError):
    """Raised when the agent ID a transport attests to does not name a known agent.

    Messages carry no agent ID of their own, so it comes from the transport instead (a
    session cookie, a connection, a relay's resolved link). This is that failing: either
    the transport attested no agent ID where the message needed an identified sender, or
    it attested one that names no agent the framework knows.
    """

    code = "UNIDENTIFIED_AGENT_ERROR"

    def __init__(self, agent_id: str | None = None):
        if agent_id is None:
            error_message = (
                "The transport attested no agent ID for a message that must come from an "
                "identified agent."
            )
        else:
            error_message = (
                f"The agent ID '{agent_id}' attested by the transport does not name a "
                f"known agent."
            )
        super().__init__(error_message=error_message, detail={"agent_id": agent_id})


class UnknownAgentTaskError(AgentIncomingMessageRejectedError):
    """Raised when a task-addressed message names a task the sending agent does not have.

    The `task_id` is the only key a message is routed by once its sender is identified,
    so a task that does not belong to that agent has nowhere to be delivered. Note that
    this is scoped to the sender: a task id that is real but another agent's is unknown
    here, and is rejected rather than crossing between agents.
    """

    code = "UNKNOWN_AGENT_TASK_ERROR"

    def __init__(self, task_id: str, agent_id: str):
        super().__init__(
            error_message=(
                f"The task ID '{task_id}' provided in the message does not name a task "
                f"belonging to the agent with the agent ID '{agent_id}'."
            ),
            detail={"task_id": task_id, "agent_id": agent_id},
        )


class UnresolvableAgentTypeError(AgentIncomingMessageRejectedError):
    """Raised when a registration's claimed agent type cannot be resolved.

    A registering agent identifies itself by exactly one of the payload it was built from
    or the agent type it claims to be, and neither is verified. This is that claim naming
    nothing the framework knows: an unknown payload ID, or an agent type name that no
    loaded agent type answers to.
    """

    code = "UNRESOLVABLE_AGENT_TYPE_ERROR"

    def __init__(self, agent_type_str: str | None = None):
        super().__init__(
            error_message=(
                f"The agent type '{agent_type_str}' claimed in the registration could "
                f"not be resolved to a known agent type."
            ),
            detail={"agent_type": agent_type_str},
        )
