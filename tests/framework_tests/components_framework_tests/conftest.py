import pytest

# Pre-load the full server module tree before the mock components import individual
# framework base classes. Several framework modules import server_singletons at module
# level, which in turn imports every service; importing it here first ensures the module
# cache is fully populated and avoids partial initialization ImportErrors.
import consortium.server.server_singletons  # noqa: F401


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
