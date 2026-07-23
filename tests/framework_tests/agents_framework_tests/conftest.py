import pytest

# Pre-load the full server module tree before any test imports individual server objects
# (for example Agent from consortium.server.objects.agent_objects). Some framework
# modules import server_singletons at module level, which in turn imports every service;
# importing it here first ensures the module cache is fully populated and avoids partial
# initialization ImportErrors when a test module imports a single server object.
import consortium.server.server_singletons  # noqa: F401


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
