from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class LifeCycleAlreadyStartedError(BaseFrameworkException):
    pass


class LifeCycleNotRunningError(BaseFrameworkException):
    pass


class LifeCycleStartError(BaseFrameworkException):
    pass


class LifeCycleRuntimeError(BaseFrameworkException):
    pass


class LifeCycleStopError(BaseFrameworkException):
    pass
