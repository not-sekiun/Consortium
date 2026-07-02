import pytest

# Pre-load the full server module tree so that individual service imports in test
# modules do not trigger circular import errors. The circular dependency exists because
# some framework modules (e.g. base_event_hook) import server_singletons at module
# level, which in turn imports every service. When tests import a single service in
# isolation the partially-initialized module cache causes ImportErrors. Importing
# server_singletons here first ensures all modules are fully cached before any test
# module tries to import individual services.
import consortium.server.server_singletons  # noqa: F401


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
