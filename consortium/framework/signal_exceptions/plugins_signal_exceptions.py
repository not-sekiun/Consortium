from consortium.framework.signal_exceptions._component_signal_exceptions import (
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)


class PluginStartError(ComponentStartError):
    pass


class PluginRuntimeError(ComponentRuntimeError):
    pass


class PluginStopError(ComponentStopError):
    pass
