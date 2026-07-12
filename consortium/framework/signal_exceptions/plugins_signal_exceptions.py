from consortium.framework.signal_exceptions._component_signal_exceptions import (
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)


class PluginStartError(ComponentStartError):
    """Raise from a start hook to abort starting the plugin with an error."""


class PluginRuntimeError(ComponentRuntimeError):
    """Raise from a runtime hook to signal that an error occurred while the plugin ran."""


class PluginStopError(ComponentStopError):
    """Raise from a stop hook to abort stopping the plugin with an error."""
