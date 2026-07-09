import contextlib
import shutil
from collections.abc import Iterator
from typing import Any

import pytest
import schemathesis
import schemathesis.python.asgi as schemathesis_asgi
from anyio.from_thread import BlockingPortal, start_blocking_portal
from starlette_testclient import TestClient

import consortium.server.server_singletons as server_singletons
from consortium.server.models.logging_models import LoggingConfigModel
from consortium.server.models.server_models import ServerConfigModel
from consortium.server.server import Server
from consortium.server.services.repository_service import RepositoryService

# This package fuzzes the REST API framework in complete isolation from tests/api_tests.
# It stands up its own Server instance and drives it entirely in-memory (no socket is ever
# bound). Because the server services are module-level singletons this suite is designed to
# be run on its own, for example with `uv run pytest tests/fuzz_tests`.
#
# Loop model (this is the crux of the setup): the Consortium server is a heavyweight
# modulith whose startup is NOT idempotent (it registers uniquely-labelled plugins and
# loads the seeded user accounts) and whose async components bind runtime tasks/primitives
# to the event loop that started them. It therefore behaves exactly like tests/api_tests:
# ONE event loop must run startup, every request and shutdown.
#
# Schemathesis' stock ASGI integration is incompatible with that: its ASGI transport wraps
# every generated example in `with starlette_testclient.TestClient(app) as client: ...`,
# and entering that context manager runs the ASGI lifespan (a full server startup AND
# shutdown) on a throwaway per-request loop. That produced a second, duplicate startup
# (DuplicatePluginLabelError, "username 'admin' already in use") and a cross-loop
# "attached to a different loop" crash on shutdown. See `patch_schemathesis_asgi_client`
# below for how both problems are removed.


class _NoLifespanTestClient(TestClient):
    # The server lifespan is driven exactly once, by hand, on the shared portal (see
    # `fuzz_server`). Entering/exiting the test client must therefore be inert: running the
    # lifespan here would start the whole server a second time and tear it down on the
    # wrong loop. Individual request calls do not need the context to be entered; they use
    # `self.portal` (set below) to reach the already-running server.
    def __enter__(self) -> "_NoLifespanTestClient":
        return self

    def __exit__(self, *args: Any) -> None:
        return None


@pytest.fixture(scope="session")
def fuzz_portal() -> Iterator[BlockingPortal]:
    # A single blocking portal backs one asyncio event loop (on a dedicated thread) for the
    # whole session. Startup, every fuzz request and shutdown are all dispatched onto this
    # loop so the server's loop-bound async state is always addressed from a consistent loop.
    with start_blocking_portal(backend="asyncio") as portal:
        yield portal


@pytest.fixture(scope="session")
def patch_schemathesis_asgi_client(fuzz_portal: BlockingPortal) -> Iterator[None]:
    # Redirect Schemathesis' ASGI client factory to our lifespan-free client, pinned to the
    # shared portal so schema loading and every generated request run on the one loop the
    # server was started on. Restored at session end for cleanliness even though this suite
    # runs on its own.
    original_get_client = schemathesis_asgi.get_client

    def get_client(app: object) -> _NoLifespanTestClient:
        client = _NoLifespanTestClient(app)
        client.portal = fuzz_portal
        return client

    schemathesis_asgi.get_client = get_client
    yield
    schemathesis_asgi.get_client = original_get_client


@pytest.fixture(scope="session")
def fuzz_server(
    tmp_path_factory: pytest.TempPathFactory,
    fuzz_portal: BlockingPortal,
) -> Iterator[tuple[Any, str]]:
    server_singletons.logging_service.configure_default_logging(
        logging_config=LoggingConfigModel(
            level="ERROR",
            log_file=None,
            rotation=None,
            retention=1,
            colorize=False,
        )
    )

    # Point the assets and artifacts repositories at throwaway temp directories before
    # startup loads their metadata so fuzzing (including the unguarded asset upload
    # endpoint) never reads from or writes to the real ./data/server directories.
    assets_directory = tmp_path_factory.mktemp("fuzz_assets_repo")
    artifacts_directory = tmp_path_factory.mktemp("fuzz_artifacts_repo")
    server_singletons.assets_service._repository_service = RepositoryService(
        repository_directory_path=assets_directory
    )
    server_singletons.assets_service.repository_directory_path = assets_directory
    server_singletons.artifacts_service._repository_service = RepositoryService(
        repository_directory_path=artifacts_directory
    )
    server_singletons.artifacts_service.repository_directory_path = artifacts_directory

    server = Server(
        server_config=ServerConfigModel(
            local_host="0.0.0.0",
            local_port=9999,
            remote_host_whitelist=[],
            remote_host_blacklist=[],
            server_header=None,
        )
    )
    server_singletons.server = server

    async def _start_and_authenticate() -> str:
        await server._server_startup_procedure()
        # The auth middleware guards every route (including /openapi.json), so a bearer
        # token is required both to load the schema and to make authorized fuzz requests.
        # `login_user` schedules a background task via `asyncio.create_task`, so it must run
        # inside a coroutine on the portal loop where a loop is running.
        user = server_singletons.users_service.login_user(
            username="admin",
            password="admin",
        )
        return user.json_web_token.to_json()["access_token"]

    # Run the one and only startup on the shared portal loop.
    token = fuzz_portal.call(_start_and_authenticate)

    yield server._app, token

    with contextlib.suppress(Exception):
        fuzz_portal.call(server._server_shutdown_procedure)
    server_singletons.server = None
    shutil.rmtree(assets_directory, ignore_errors=True)
    shutil.rmtree(artifacts_directory, ignore_errors=True)


@pytest.fixture(scope="session")
def fuzz_auth_headers(fuzz_server: tuple[Any, str]) -> dict[str, str]:
    _app, token = fuzz_server
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def fuzz_api_schema(
    fuzz_server: tuple[Any, str],
    patch_schemathesis_asgi_client: None,
):
    app, token = fuzz_server
    api_schema = schemathesis.openapi.from_asgi(
        "/openapi.json",
        app,
        headers={"Authorization": f"Bearer {token}"},
    )
    # Exclude endpoints that would corrupt the shared authenticated session the whole suite
    # relies on. `POST /api/logout` invalidates the bearer token used for every other
    # request, and `POST /api/user-accounts` mutates the seeded account list. `path_regex`
    # is anchored so only these exact operations are dropped (not the parameterised
    # `/api/logout/user/{user_id}` style routes, which are guarded by a path parameter and
    # therefore safe to fuzz). Every other mutating endpoint is addressed by a path
    # parameter, and the random UUID4s Hypothesis generates never collide with seeded
    # resources, so those remain safe to fuzz.
    api_schema = api_schema.exclude(method="POST", path_regex=r"^/api/logout$")
    api_schema = api_schema.exclude(method="POST", path_regex=r"^/api/user-accounts$")
    return api_schema
