from consortium.framework.exceptions._life_cycle_exceptions import (
    LifeCycleRuntimeError,
    LifeCycleStartError,
    LifeCycleStopError,
)


class PluginStartError(LifeCycleStartError):
    pass


class PluginRuntimeError(LifeCycleRuntimeError):
    pass


class PluginStopError(LifeCycleStopError):
    pass
