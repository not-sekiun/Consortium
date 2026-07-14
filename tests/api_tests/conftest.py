import json
import pathlib
import shutil
from collections.abc import Iterator

import httpx
import pytest

import consortium.server.server_singletons as server_singletons
from consortium.server.models.logging_models import LoggingConfigModel
from consortium.server.models.server_models import ServerConfigModel
from consortium.server.server import Server
from consortium.server.services.repository_service import RepositoryService

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


# assets_service and artifacts_service in server_singletons.py are module-level
# singletons pointed at the real ./data/server/assets and ./data/server/artifacts
# directories, and _server_startup_procedure loads their repository metadata on
# startup. Since `app` is a single session-scoped fixture shared by every api_tests
# module, the redirect must happen before `app` starts the server (see the `app`
# fixture's dependency below) so no test run ever touches the real data directories.
@pytest.fixture(scope="session")
def throwaway_assets_and_artifacts_repositories(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[None]:
    original_assets_repository_service = (
        server_singletons.assets_service._repository_service
    )
    original_artifacts_repository_service = (
        server_singletons.artifacts_service._repository_service
    )

    assets_directory = tmp_path_factory.mktemp("assets_repo")
    artifacts_directory = tmp_path_factory.mktemp("artifacts_repo")
    server_singletons.assets_service._repository_service = RepositoryService(
        repository_directory_path=assets_directory
    )
    server_singletons.assets_service.repository_directory_path = assets_directory
    server_singletons.artifacts_service._repository_service = RepositoryService(
        repository_directory_path=artifacts_directory
    )
    server_singletons.artifacts_service.repository_directory_path = artifacts_directory

    yield

    server_singletons.assets_service._repository_service = (
        original_assets_repository_service
    )
    server_singletons.assets_service.repository_directory_path = (
        original_assets_repository_service.repository_directory_path
    )
    server_singletons.artifacts_service._repository_service = (
        original_artifacts_repository_service
    )
    server_singletons.artifacts_service.repository_directory_path = (
        original_artifacts_repository_service.repository_directory_path
    )
    shutil.rmtree(assets_directory, ignore_errors=True)
    shutil.rmtree(artifacts_directory, ignore_errors=True)


@pytest.fixture(scope="session")
async def app(configure_logging, throwaway_assets_and_artifacts_repositories):
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
        await server_singletons.listener_profiles_service.load_listener_profile_from_listener_profile_project_folder(
            listener_profile_project_folder=mock_root / folder,
        )


@pytest.fixture(scope="session")
async def load_mock_agent_profiles(app):
    mock_root = pathlib.Path(__file__).parent / "mocks"
    for folder in ("mock_agent_1", "mock_agent_2"):
        await server_singletons.agent_profiles_service.load_agent_profile_from_agent_profile_project_folder(
            agent_profile_project_folder=mock_root / folder,
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
            json={name: opt["default_value"] for name, opt in options.items()},
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
        json={name: opt["default_value"] for name, opt in options.items()},
    )
    assert create_response.status_code == 201, (
        f"Failed to create mock listener: {create_response.text}"
    )
    listener_id = create_response.json()["listener_id"]

    # Register an agent directly via the service; no listener start is required.
    agent = server_singletons.agents_service.register_agent(
        listener_id=listener_id,
        agent_type="mock_alpha",
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
