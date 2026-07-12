from consortium.framework.signal_exceptions.base_signal_exception import (
    BaseSignalException,
)


# Event hooks don't share component lifecycle logic with other components like listeners
# plugins or agent generators so they cannot properly make use of the Component class of
# framework errors. Therefore, we define their own set of exceptions to be raised and
# handled by the event hook registry service
class EventHookSetupError(BaseSignalException):
    """Raise from `on_setup` to abort loading the event hook with an error."""


class EventHookTriggerError(BaseSignalException):
    """Raise from `on_triggered` to signal that handling a triggered event failed."""


class EventHookTeardownError(BaseSignalException):
    """Raise from `on_teardown` to abort unloading the event hook with an error."""
