import json
import pathlib
import shutil
from collections.abc import Iterator

import httpx
import pytest

import consortium.server.server_singletons as server_singletons
from consortium.framework.agents.agent_message_models import RegistrationMessageModel
from consortium.server.api import login_api, websockets_api
from consortium.server.models.logging_models import LoggingConfigModel
from consortium.server.models.server_models import ServerConfigModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server import Server
from consortium.server.services import websocket_tickets_service as tickets_module
from consortium.server.services.repository_service import RepositoryService
from tests.api_tests.websocket_helpers import FakeClock, WebSocketSession

_MOCK_LISTENER_LABELS = {"consortium.listeners.mock_1", "consortium.listeners.mock_2"}
_MOCK_AGENT_LABELS = {"consortium.agents.mock_1", "consortium.agents.mock_2"}

_JSON_WEB_TOKEN_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "access_token": {"type": "string"},
        "token_type": {"type": "string"},
    },
    "required": ["access_token", "token_type"],
}


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def validate_user_accounts_json_file_before_tests():
    default_user_accounts = [
        {"username": "admin", "password": "admin", "role": "ADMIN"},
        {"username": "operator", "password": "operator", "role": "OPERATOR"},
        {"username": "spectator", "password": "spectator", "role": "SPECTATOR"},
    ]
    with open("data/server/user_accounts.json") as file:
        user_accounts_json_data = json.load(file)
    for user_account in user_accounts_json_data:
        assert user_account in default_user_accounts


@pytest.fixture(scope="session", autouse=True)
def validate_server_config_json_file_before_tests():
    default_server_config = {
        "local_host": "0.0.0.0",
        "local_port": 9999,
        "remote_host_whitelist": [],
        "remote_host_blacklist": [],
        "server_header": None,
    }
    with open("data/server/server_config.json") as file:
        server_config_json_data = json.load(file)
    for key, value in default_server_config.items():
        assert server_config_json_data[key] == value


# The rate limited endpoints (login at 5/minute, websocket ticket issuance at 20/minute)
# are keyed on the remote address, and every request made through httpx.ASGITransport
# shares a single address. The session clients below, any fixture that re-logs them in,
# and any test that asks for several tickets would otherwise exhaust those buckets and
# start getting 429s. Each Limiter is a module-level singleton whose `enabled` flag is
# read per request, so flipping them here disables the limits for the whole test session.
@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiters() -> Iterator[None]:
    rate_limited_api_modules = (login_api, websockets_api)
    for api_module in rate_limited_api_modules:
        api_module.limiter.enabled = False
    yield
    for api_module in rate_limited_api_modules:
        api_module.limiter.enabled = True


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    consortium_root = pathlib.Path(__file__).parents[2]
    log_file = str(
        consortium_root
        / "data"
        / "server"
        / "logs"
        / "{time:YYYY-MM-DDTHH-mm-ss}.test.log"
    )
    server_singletons.logging_service.configure_default_logging(
        logging_config=LoggingConfigModel(
            level="WARNING",
            log_file=log_file,
            rotation=None,
            retention=1,
            colorize=True,
        )
    )


# assets_service, artifacts_service and payloads_service in server_singletons.py are
# module-level singletons pointed at the real ./data/server/{assets,artifacts,payloads}
# directories, and _server_startup_procedure loads their repository metadata on
# startup. Since `app` is a single session-scoped fixture shared by every api_tests
# module, the redirect must happen before `app` starts the server (see the `app`
# fixture's dependency below) so no test run ever touches the real data directories.
@pytest.fixture(scope="session")
def throwaway_repositories(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[None]:
    services_and_temp_names = [
        (server_singletons.assets_service, "assets_repo"),
        (server_singletons.artifacts_service, "artifacts_repo"),
        (server_singletons.payloads_service, "payloads_repo"),
    ]

    original_repository_services = {
        id(service): service._repository_service
        for service, _ in services_and_temp_names
    }
    throwaway_directories = []
    for service, temp_name in services_and_temp_names:
        directory = tmp_path_factory.mktemp(temp_name)
        throwaway_directories.append(directory)
        service._repository_service = RepositoryService(
            repository_directory_path=directory
        )
        service.repository_directory_path = directory

    yield

    for service, _ in services_and_temp_names:
        original_repository_service = original_repository_services[id(service)]
        service._repository_service = original_repository_service
        service.repository_directory_path = (
            original_repository_service.repository_directory_path
        )
    for directory in throwaway_directories:
        shutil.rmtree(directory, ignore_errors=True)


@pytest.fixture(scope="session")
async def app(configure_logging, throwaway_repositories, disable_rate_limiters):
    """Initialize the FastAPI app once for the entire test session."""
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
    await server._server_startup_procedure()
    yield server._app
    await server._server_shutdown_procedure()
    server_singletons.server = None


@pytest.fixture(scope="session")
async def admin_client(app):
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    )
    response = await client.post(
        "/api/login",
        data={"username": "admin", "password": "admin"},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    yield client
    await client.aclose()


@pytest.fixture(scope="session")
async def operator_client(app):
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    )
    response = await client.post(
        "/api/login",
        data={"username": "operator", "password": "operator"},
    )
    assert response.status_code == 200, f"Operator login failed: {response.text}"
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    yield client
    await client.aclose()


@pytest.fixture(scope="session")
async def spectator_client(app):
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    )
    response = await client.post(
        "/api/login",
        data={"username": "spectator", "password": "spectator"},
    )
    assert response.status_code == 200, f"Spectator login failed: {response.text}"
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    yield client
    await client.aclose()


@pytest.fixture(params=["admin", "operator", "spectator"])
def client(admin_client, operator_client, spectator_client, request):
    return {
        "admin": admin_client,
        "operator": operator_client,
        "spectator": spectator_client,
    }[request.param]


@pytest.fixture(scope="session")
async def load_mock_listener_profiles(app):
    mock_root = pathlib.Path(__file__).parent / "mocks"
    for folder in ("mock_listener_1", "mock_listener_2"):
        await server_singletons.listener_profiles_service.load_listener_profile_from_directory(
            directory=mock_root / folder,
        )


@pytest.fixture(scope="session")
async def load_mock_agent_profiles(app):
    mock_root = pathlib.Path(__file__).parent / "mocks"
    for folder in ("mock_agent_1", "mock_agent_2"):
        await (
            server_singletons.agent_profiles_service.load_agent_profile_from_directory(
                directory=mock_root / folder,
            )
        )


@pytest.fixture
async def mock_listener_template_ids(admin_client, load_mock_listener_profiles):
    templates_response = await admin_client.get("/api/listener-templates/all")
    return [
        t["listener_template_id"]
        for t in templates_response.json()
        if t["label"] in _MOCK_LISTENER_LABELS
    ]


@pytest.fixture
async def mock_agent_template_ids(admin_client, load_mock_agent_profiles):
    templates_response = await admin_client.get("/api/agent-templates/all")
    return [
        t["agent_template_id"]
        for t in templates_response.json()
        if t["label"] in _MOCK_AGENT_LABELS
    ]


@pytest.fixture
async def create_listeners_before_test(admin_client, load_mock_listener_profiles):
    templates_response = await admin_client.get("/api/listener-templates/all")
    for template in templates_response.json():
        if template["label"] not in _MOCK_LISTENER_LABELS:
            continue
        template_id = template["listener_template_id"]
        detail_response = await admin_client.get(
            f"/api/listener-templates/{template_id}"
        )
        options = detail_response.json()["options"]
        await admin_client.post(
            f"/api/listener-templates/{template_id}",
            json={
                "options": {
                    name: opt["default_value"] for name, opt in options.items()
                },
            },
        )
    yield


@pytest.fixture
async def delete_listeners_after_test(admin_client):
    yield
    response = await admin_client.get("/api/listeners/all")
    for listener in response.json():
        listener_id = listener["listener_id"]
        # stop the listener first; ignore 409 (not running) and other non-fatal errors
        stop_response = await admin_client.post(f"/api/listeners/{listener_id}/stop")
        if stop_response.status_code not in (202, 409):
            await admin_client.post(f"/api/listeners/{listener_id}/cancel")
        await admin_client.delete(f"/api/listeners/{listener_id}")


@pytest.fixture
async def mock_agent(
    admin_client, load_mock_listener_profiles, load_mock_agent_profiles
):
    # Find the mock_1 listener template and create a listener from its default options.
    templates_response = await admin_client.get("/api/listener-templates/all")
    template = next(
        t
        for t in templates_response.json()
        if t["label"] == "consortium.listeners.mock_1"
    )
    template_id = template["listener_template_id"]
    detail_response = await admin_client.get(f"/api/listener-templates/{template_id}")
    options = detail_response.json()["options"]
    create_response = await admin_client.post(
        f"/api/listener-templates/{template_id}",
        json={
            "options": {name: opt["default_value"] for name, opt in options.items()},
        },
    )
    assert create_response.status_code == 201, (
        f"Failed to create mock listener: {create_response.text}"
    )
    listener_id = create_response.json()["listener_id"]

    # Register an agent directly via the service; no listener start is required.
    agent = server_singletons.agents_service.register_agent(
        listener_id=listener_id,
        registration_message=RegistrationMessageModel(agent_type="mock_alpha"),
        name="test-agent",
    )
    agent_id = str(agent.agent_id)

    yield {"agent_id": agent_id, "listener_id": listener_id}

    # Deregister the agent before deleting the listener to avoid orphan state.
    try:
        server_singletons.agents_service.deregister_agent_by_agent_id(agent_id=agent_id)
    except Exception:
        pass
    await admin_client.delete(f"/api/listeners/{listener_id}")


@pytest.fixture
async def delete_agent_generators_after_test(admin_client):
    yield
    response = await admin_client.get("/api/agent-generators/all")
    for ag in response.json():
        await admin_client.delete(f"/api/agent-generators/{ag['agent_generator_id']}")


@pytest.fixture
async def restore_default_user_accounts_after_test(
    admin_client, operator_client, spectator_client
):
    yield
    all_response = await admin_client.get("/api/user-accounts/all")
    for ua in all_response.json():
        await admin_client.delete(f"/api/user-accounts/{ua['user_account_id']}")
    for username, password, role in [
        ("admin", "admin", "ADMIN"),
        ("operator", "operator", "OPERATOR"),
        ("spectator", "spectator", "SPECTATOR"),
    ]:
        await admin_client.post(
            "/api/user-accounts",
            json={"username": username, "password": password, "role": role},
        )
    # Re-login each client to get new JWTs linked to the newly created UserAccount
    # UUIDs. Login is idempotent so no logout is required first.
    for client, username, password in [
        (admin_client, "admin", "admin"),
        (operator_client, "operator", "operator"),
        (spectator_client, "spectator", "spectator"),
    ]:
        response = await client.post(
            "/api/login", data={"username": username, "password": password}
        )
        if response.status_code == 200:
            client.headers["Authorization"] = (
                f"Bearer {response.json()['access_token']}"
            )


@pytest.fixture(scope="session", autouse=True)
async def logout_all_sessions(admin_client, operator_client, spectator_client):
    yield
    await admin_client.post("/api/logout")
    await operator_client.post("/api/logout")
    await spectator_client.post("/api/logout")


@pytest.fixture(scope="session", autouse=True)
def restore_user_accounts_file_after_tests():
    yield
    default_user_accounts = [
        {"username": "admin", "password": "admin", "role": "ADMIN"},
        {"username": "operator", "password": "operator", "role": "OPERATOR"},
        {"username": "spectator", "password": "spectator", "role": "SPECTATOR"},
    ]
    with open("data/server/user_accounts.json", "w") as file:
        json.dump(default_user_accounts, file, indent=4)


# ---------------------------------------------------------------------------
# WebSocket handshake fixtures
#
# Shared by test_events_api.py and test_websocket_authentication_e2e.py: both drive the
# /api/ws/events handshake through the same ASGI transport, controllable clock, and
# permission-stripping fixture, so these live in conftest as the single source of truth.
# ---------------------------------------------------------------------------


@pytest.fixture
async def ws_factory(app):
    """
    Factory fixture for creating `WebSocketSession` instances bound to `app`.

    Every session produced by the returned factory is tracked and closed
    automatically on teardown, so tests no longer need to call `await
    ws.close()` themselves (closing early inside a test, e.g. to assert
    post-disconnect behavior, still works fine - `close()` is a no-op on an
    already-finished session).
    """
    sessions: list[WebSocketSession] = []

    def _make() -> WebSocketSession:
        ws = WebSocketSession(app)
        sessions.append(ws)
        return ws

    yield _make

    for ws in sessions:
        await ws.close()


@pytest.fixture
async def ws(ws_factory):
    """A single, unopened `WebSocketSession` for tests that need only one."""
    return ws_factory()


@pytest.fixture
def ticket_clock(monkeypatch):
    """Replaces the clock the tickets service reads, for the test's duration."""
    fake_clock = FakeClock()
    # The service's whole `time` name is swapped rather than `time.monotonic` being
    # patched on the real `time` module (which is what the service unit tests do). These
    # tests drive an asyncio event loop, and the loop reads `time.monotonic` for its own
    # timers: moving the real clock forward by a ticket lifetime would fire every pending
    # timeout in the loop as a side effect. Swapping the name confines the fake to the one
    # module under test. The service uses `time` for nothing but `monotonic`.
    monkeypatch.setattr(tickets_module, "time", fake_clock)
    return fake_clock


@pytest.fixture
async def spectator_role_without_events_websocket_permission(spectator_client):
    """Strips USE_EVENTS_WEBSOCKET from the spectator's role for the test's duration.

    All three default roles hold the permission, so a role that lacks it has to be
    manufactured. Only the authorization service's in-memory mapping is touched:
    `save_server_role_permissions` is never called, so data/server/role_permissions.json
    is left exactly as it was on disk.
    """
    role = (await spectator_client.get("/api/users/me")).json()["role"]
    permission = str(UserPermissions.USE_EVENTS_WEBSOCKET)
    authorization_service = server_singletons.authorization_service

    authorization_service.remove_permission_from_role(
        role=role,
        permission=permission,
    )
    assert not authorization_service.has_permission(role, permission)

    yield role

    authorization_service.add_permission_to_role(role=role, permission=permission)
