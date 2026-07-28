from enum import StrEnum


class EventType(StrEnum):
    """Framework-wide event identifiers used to subscribe event hooks to specific occurrences.

    Use these values in BaseEventHook.event_types to declare which events the hook
    should be triggered by. Events cover server lifecycle, listener and agent generator
    state changes, agent activity, user sessions, and resource (payload, asset, artifact)
    CRUD operations.

    Attributes:
        START_SERVER: The server is starting.
        STOP_SERVER: The server is stopping.
        LISTENER_CREATED: A listener instance is created.
        LISTENER_ADDED: A listener is added to the server.
        LISTENER_UPDATED: A listener's configuration is updated.
        LISTENER_REMOVED: A listener is removed from the server.
        LISTENER_STARTED: A listener starts.
        LISTENER_STOPPED: A listener stops.
        LISTENER_CANCELLED: A listener is cancelled.
        AGENT_GENERATOR_CREATED: An agent generator instance is created.
        AGENT_GENERATOR_ADDED: An agent generator is added to the server.
        AGENT_GENERATOR_UPDATED: An agent generator's configuration is updated.
        AGENT_GENERATOR_REMOVED: An agent generator is removed from the server.
        AGENT_GENERATOR_STARTED: An agent generator starts.
        AGENT_GENERATOR_STOPPED: An agent generator stops.
        AGENT_GENERATOR_CANCELLED: An agent generator is cancelled.
        AGENT_REGISTERED: An agent registers with the server.
        AGENT_CHECKED_IN: An agent checks in with the server.
        AGENT_UPDATED: An agent's metadata is updated.
        AGENT_DEREGISTERED: An agent deregisters from the server.
        AGENT_DELETED: An agent is deleted.
        AGENT_TASKED: A task is assigned to an agent.
        AGENT_TASK_COMPLETED: An agent completes a task.
        USER_LOGGED_IN: A user signs in.
        USER_LOGGED_OUT: A user signs out.
        PAYLOAD_CREATED: A payload is created.
        PAYLOAD_UPDATED: A payload is updated.
        PAYLOAD_DELETED: A payload is deleted.
        ASSET_CREATED: An asset is created.
        ASSET_UPDATED: An asset is updated.
        ASSET_DELETED: An asset is deleted.
        ARTIFACT_CREATED: An artifact is created.
        ARTIFACT_UPDATED: An artifact is updated.
        ARTIFACT_DELETED: An artifact is deleted.
        LISTENER_RUNTIME_ERRORED: A listener runtime error occurs.
        AGENT_GENERATOR_RUNTIME_ERRORED: An agent-generator runtime error occurs.
    """

    START_SERVER = "START_SERVER"
    STOP_SERVER = "STOP_SERVER"

    LISTENER_CREATED = "LISTENER_CREATED"
    LISTENER_ADDED = "LISTENER_ADDED"
    LISTENER_UPDATED = "LISTENER_UPDATED"
    LISTENER_REMOVED = "LISTENER_REMOVED"
    LISTENER_STARTED = "LISTENER_STARTED"
    LISTENER_STOPPED = "LISTENER_STOPPED"
    LISTENER_CANCELLED = "LISTENER_CANCELLED"

    AGENT_GENERATOR_CREATED = "AGENT_GENERATOR_CREATED"
    AGENT_GENERATOR_ADDED = "AGENT_GENERATOR_ADDED"
    AGENT_GENERATOR_UPDATED = "AGENT_GENERATOR_UPDATED"
    AGENT_GENERATOR_REMOVED = "AGENT_GENERATOR_REMOVED"
    AGENT_GENERATOR_STARTED = "AGENT_GENERATOR_STARTED"
    AGENT_GENERATOR_STOPPED = "AGENT_GENERATOR_STOPPED"
    AGENT_GENERATOR_CANCELLED = "AGENT_GENERATOR_CANCELLED"

    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_CHECKED_IN = "AGENT_CHECKED_IN"
    AGENT_UPDATED = "AGENT_UPDATED"
    AGENT_DEREGISTERED = "AGENT_DEREGISTERED"
    AGENT_DELETED = "AGENT_DELETED"
    AGENT_TASKED = "AGENT_TASKED"
    AGENT_TASK_COMPLETED = "AGENT_TASK_COMPLETED"

    USER_LOGGED_IN = "USER_LOGGED_IN"
    USER_LOGGED_OUT = "USER_LOGGED_OUT"

    PAYLOAD_CREATED = "PAYLOAD_CREATED"
    PAYLOAD_UPDATED = "PAYLOAD_UPDATED"
    PAYLOAD_DELETED = "PAYLOAD_DELETED"

    ASSET_CREATED = "ASSET_CREATED"
    ASSET_UPDATED = "ASSET_UPDATED"
    ASSET_DELETED = "ASSET_DELETED"

    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    ARTIFACT_UPDATED = "ARTIFACT_UPDATED"
    ARTIFACT_DELETED = "ARTIFACT_DELETED"

    # TODO: Implement the rest of these events
    LISTENER_RUNTIME_ERRORED = "LISTENER_RUNTIME_ERRORED"
    AGENT_GENERATOR_RUNTIME_ERRORED = "AGENT_GENERATOR_RUNTIME_ERRORED"
