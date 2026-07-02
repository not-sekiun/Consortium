from consortium.framework.exceptions.base_framework_exception import (
    BaseRaiseOnlyFrameworkException,
)


# Event hooks don't share component lifecycle logic with other components like listeners
# plugins or agent generators so they cannot properly make use of the Component class of
# framework errors. Therefore, we define their own set of exceptions to be raised and
# handled by the event hook registry service
class EventHookSetupError(BaseRaiseOnlyFrameworkException):
    """
    Raise this exception from `on_setup()` to signal that an error occurred while the
    event hook was setting up and to abort loading it.
    """


class EventHookTriggerError(BaseRaiseOnlyFrameworkException):
    """
    Raise this exception from `on_triggered()` to signal that an error occurred while
    handling a triggered event.
    """


class EventHookTeardownError(BaseRaiseOnlyFrameworkException):
    """
    Raise this exception from `on_teardown()` to signal that an error occurred while the
    event hook was tearing down and to abort unloading it.
    """
