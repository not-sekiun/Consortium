# Complete Event Hook Example

Here is the complete Agent Activity Tracker event hook combining all of the concepts
covered in [Project Setup](project-setup.md) through
[Event Hook Conventions](event-hook-conventions.md):

```python
import json

from consortium.framework.event_hooks import BaseEventHook, EventType


class EventHook(BaseEventHook):
  label = "consortium.event_hooks.agent_activity_tracker"
  name = "Agent Activity Tracker"
  description = (
    "Counts agent lifecycle events and writes a session summary "
    "to a JSON file on teardown."
  )
  version = "0.1.0"
  compatible_framework_version = ">=0.1.0"
  authors = {"Your Name"}
  event_types = {
    EventType.AGENT_REGISTERED,
    EventType.AGENT_CHECKED_IN,
    EventType.AGENT_TASKED,
    EventType.AGENT_TASK_COMPLETED,
    EventType.AGENT_DEREGISTERED,
  }

  async def on_setup(self) -> None:
    self.environment.counts = {
      EventType.AGENT_REGISTERED: 0,
      EventType.AGENT_CHECKED_IN: 0,
      EventType.AGENT_TASKED: 0,
      EventType.AGENT_TASK_COMPLETED: 0,
      EventType.AGENT_DEREGISTERED: 0,
    }
    self.logger.info("Agent Activity Tracker is ready.")

  async def on_triggered(self, event) -> None:
    self._record_event(event)

    if event.event_type == EventType.AGENT_REGISTERED:
      self.logger.success("New agent connected: {}", event.message)
    elif event.event_type == EventType.AGENT_DEREGISTERED:
      self.logger.info("Agent disconnected: {}", event.message)
    elif event.event_type == EventType.AGENT_TASKED:
      self.logger.info("Task dispatched: {}", event.message)
    elif event.event_type == EventType.AGENT_TASK_COMPLETED:
      self.logger.success("Task completed: {}", event.message)
    else:
      self.logger.debug("[{}] {}", event.event_type, event.message)

  async def on_teardown(self) -> None:
    summary_path = self.root_directory / "last_session_summary.json"
    summary = {
      str(event_type): count
      for event_type, count in self.environment.counts.items()
    }
    with summary_path.open("w") as f:
      json.dump(summary, f, indent=2)
    self.logger.info("Session summary written to '{}'.", summary_path)

  def _record_event(self, event) -> None:
    if event.event_type in self.environment.counts:
      self.environment.counts[event.event_type] += 1
```

## Further examples

`consortium/components/event_hooks/webhook_sender/event_hook.py` is the most complete
reference implementation available. Beyond the basic pattern above, it demonstrates:

- Validating config against a JSON schema in `on_setup` using `jsonschema`
- Dynamic subscription at setup time from a config file, via
  `subscribe_to_event_type()`
- Async HTTP requests with retry logic in a private helper
- Handling multiple webhook platform formats inside `on_triggered`
- Raising `EventHookSetupError` and `EventHookTriggerError` (see
  [Event Hook Setup](event-hook-setup.md) and
  [Event Hook Triggering](event-hook-triggering.md)) instead of logging and continuing
  with partial state
