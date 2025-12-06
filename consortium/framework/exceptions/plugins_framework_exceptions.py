from consortium.framework.exceptions._component_framework_exceptions import (
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
