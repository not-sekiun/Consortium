import json
import pathlib

import httpx
import pytest

from consortium.server import server_singletons
from consortium.server.models.config_models import LoggingConfigModel, ServerConfigModel
from consortium.server.server import Server
from consortium.server.server_logging import configure_logger

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
    configure_logger(
        LoggingConfigModel(
            level="WARNING",
            log_file=log_file,
            rotation=None,
            retention=1,
            colorize=True,
        )
    )


@pytest.fixture(scope="session")
async def app(configure_logging):
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


@pytest.fixture
async def create_listeners_before_test(admin_client):
    templates_response = await admin_client.get("/api/listener-templates/all")
    for template in templates_response.json():
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
        await admin_client.delete(f"/api/listeners/{listener['listener_id']}")


@pytest.fixture
async def delete_agent_generators_after_test(admin_client):
    yield
    response = await admin_client.get("/api/agent-generators/all")
    for ag in response.json():
        await admin_client.delete(f"/api/agent-generators/{ag['agent_generator_id']}")


@pytest.fixture
async def restore_default_user_accounts_after_test(admin_client):
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
