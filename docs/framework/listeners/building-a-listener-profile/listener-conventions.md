# Listener Conventions

## Private methods

Underscore-prefixed methods are private: internal helpers not intended to be called from
outside the class. The session handlers from the running loop (`_handle_session`,
`_handle_registration`, `_handle_check_in`, `_handle_result`) are all private. The public
interface of a listener is the set of lifecycle hooks the framework calls (`on_started`,
`on_running`, `on_stopped`, `on_cancelled`, `on_errored`, `on_fatal`). Helpers that do
not need `self` should be `@staticmethod`.

## Runtime state on self.environment

Do not set runtime state as direct instance attributes (`self.server = ...`). Use
`self.environment` instead. This keeps runtime state clearly separate from the
framework-managed attributes on `self`, and lets `on_stopped` and `on_cancelled` reach
that state safely even when cancellation arrives before `on_running()` finished
initialising.

## What lives on self

| Attribute                         | Type                     | Description                                                    |
|-----------------------------------|--------------------------|----------------------------------------------------------------|
| `self.listener_id`                | `uuid.UUID`              | Unique identifier for this listener instance                   |
| `self.name`                       | `str`                    | Display name set at creation time                              |
| `self.description`                | `str`                    | Description set at creation time                               |
| `self.endpoint`                   | `str`                    | Network endpoint derived by `resolve_listener_endpoint`        |
| `self.listener_type`              | `BaseListenerType`       | Type descriptor (class attribute)                              |
| `self.parameters`                 | `dict`                   | Resolved option values from the template                       |
| `self.datetime_created`           | `datetime`               | Creation timestamp                                             |
| `self.environment`                | `SimpleNamespace`        | Mutable runtime state; use this instead of instance attributes |
| `self.connected_agents_service`   | `ConnectedAgentsService` | Agent lifecycle interface                                      |
| `self.connected_agents`           | `list[Agent]`            | Property: agents currently connected to this listener          |
| `self.stop_event`                 | `asyncio.Event`          | Set when `stop()` is called from outside                       |
| `self.status`                     | `Status`                 | Lifecycle status; `.state` holds the current state string      |
| `self.logger`                     | `loguru.Logger`          | Listener-scoped logger                                         |
| `self.services`                   | namespace                | All framework services                                         |
| `self.creating_listener_template` | `BaseListenerTemplate`   | Template that created this instance (class attribute)          |

## ConnectedAgentsService methods

The three [protocol obligations](listener-protocol.md) are fulfilled through
`self.connected_agents_service`. Its full method surface:

| Method                                                                          | Sync/Async | Description                                                              |
|---------------------------------------------------------------------------------|------------|--------------------------------------------------------------------------|
| `register_agent(payload_id=..., agent_type=..., ...)`                           | sync       | Create an agent record; supply either `payload_id` or `agent_type`       |
| `get_next_task_message_by_task_id(agent_id, task_id, timeout)`                  | async      | Read the next message for one task's outbox                              |
| `get_next_task_message_sequential(agent_id, timeout)`                           | async      | Drain one outbox completely before moving to the next                    |
| `get_next_task_message_any(agent_id, timeout)`                                  | async      | Mux the next available message from any task outbox                      |
| `drain_task_messages_by_task_id(agent_id, task_id)`                             | async gen  | Yield every remaining message for one task                               |
| `drain_task_messages_sequential(agent_id)`                                     | async gen  | Yield task messages one outbox at a time                                 |
| `drain_task_messages_any(agent_id)`                                            | async gen  | Yield muxed messages from all task outboxes                              |
| `dispatch_task_output_message(agent_id, task_id, success, message, data, payload)` | async   | Route a result into its task-specific inbox; auto check-in               |
| `deregister_agent_by_agent_id(agent_id)`                                        | sync       | Remove the agent from the framework entirely                             |
| `check_in_agent_by_agent_id(agent_id)`                                          | sync       | Record a manual check-in without reading or submitting task messages     |
| `get_all_agents()`                                                              | sync       | All agents connected to this listener                                    |
| `get_agent_by_agent_id(agent_id)`                                               | sync       | Look up a single agent; validates it belongs to this listener            |

Choose the reader that matches the wire protocol. Sequential, muxed, and task-specific
delivery are all canonical patterns. `timeout=None` waits indefinitely, while
`timeout=0` performs a non-blocking poll.

See the [Complete Listener Profile](complete-listener-profile.md) for all of these
concepts combined into one working profile.
