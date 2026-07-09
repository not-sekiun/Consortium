import pathlib
import uuid
from unittest.mock import MagicMock, patch

import pytest

from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions import (
    AgentTemplateLabelNotFoundError,
)
from consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions import (
    PayloadNotFoundError,
)
from consortium.server.services.agent_templates_service import AgentTemplatesService
from consortium.server.services.events_service import EventsService
from consortium.server.services.payloads_service import PayloadsService
from consortium.server.services.repository_service import RepositoryService


@pytest.fixture
def repo_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    d = tmp_path / "payloads_repo"
    d.mkdir()
    return d


@pytest.fixture
def repo_service(repo_dir: pathlib.Path) -> RepositoryService:
    return RepositoryService(repository_directory_path=repo_dir)


@pytest.fixture
def events_service() -> MagicMock:
    mock = MagicMock(spec=EventsService)
    mock.trigger_event = MagicMock(return_value=MagicMock())
    return mock


@pytest.fixture
def agent_templates_service() -> MagicMock:
    return MagicMock(spec=AgentTemplatesService)


@pytest.fixture
def service(
    events_service: MagicMock,
    repo_service: RepositoryService,
    agent_templates_service: MagicMock,
) -> PayloadsService:
    return PayloadsService(
        events_service=events_service,
        repository_service=repo_service,
        agent_templates_service=agent_templates_service,
    )


def _make_mock_payload(payload_id: str | None = None) -> MagicMock:
    # Build a mock Payload with the minimum attributes accessed by PayloadsService
    p = MagicMock()
    p.payload_id = uuid.UUID(payload_id) if payload_id else uuid.uuid4()
    p.agent_template = MagicMock()
    p.agent_template.label = "test.label"
    p.build_parameters = {}
    p.payload_data = {}
    p.to_json.return_value = {"payload_id": str(p.payload_id)}
    return p


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_repr(service: PayloadsService):
    assert "PayloadsService" in repr(service)


# ---------------------------------------------------------------------------
# load_repository_metadata (forwarding)
# ---------------------------------------------------------------------------


def test_load_repository_metadata_delegates(
    service: PayloadsService, repo_dir: pathlib.Path
):
    service.load_repository_metadata()
    assert (repo_dir / ".repository.json").exists()


# ---------------------------------------------------------------------------
# save_repository_metadata (forwarding)
# ---------------------------------------------------------------------------


def test_save_repository_metadata_delegates(
    service: PayloadsService, repo_dir: pathlib.Path
):
    # Call load first so the metadata file exists, then save
    service.load_repository_metadata()
    service.save_repository_metadata()
    assert (repo_dir / ".repository.json").exists()


# ---------------------------------------------------------------------------
# load_payloads_metadata
# ---------------------------------------------------------------------------


def test_load_payloads_metadata_empty_repository_leaves_payloads_empty(
    service: PayloadsService,
):
    # No repository resources means no payloads to reconstruct and no separate
    # payloads metadata file is created.
    service.load_repository_metadata()
    service.load_payloads_metadata()
    assert service.get_all_payloads() == []
    assert not (service.repository_directory_path / ".payloads.json").exists()


def test_load_payloads_metadata_rebuilds_payloads_from_resource_data(
    service: PayloadsService,
    repo_service: RepositoryService,
    agent_templates_service: MagicMock,
):
    # A payload's metadata is persisted in the `data` field of its repository resource
    with patch("asyncio.create_task"):
        resource = repo_service.create_file(
            content="payload",
            name="p.bin",
            data={
                "agent_template": "test.label",
                "build_parameters": {"foo": "bar"},
                "payload_data": {"baz": 1},
            },
        )
    payload_id = str(resource.resource_id)

    agent_template = MagicMock(spec=BaseAgentTemplate)
    agent_template.label = "test.label"
    agent_template.agent_type = MagicMock()
    agent_templates_service.get_agent_template_by_label.return_value = agent_template

    service.load_payloads_metadata()

    payload = service.get_payload_by_payload_id(payload_id=payload_id)
    assert payload.build_parameters == {"foo": "bar"}
    assert payload.payload_data == {"baz": 1}
    assert payload.agent_template is agent_template


def test_load_payloads_metadata_skips_resource_missing_payload_fields(
    service: PayloadsService, repo_service: RepositoryService
):
    # A resource whose `data` field lacks the expected payload keys is skipped
    with patch("asyncio.create_task"):
        repo_service.create_file(content="not a payload", name="x.bin")
    service.load_payloads_metadata()
    assert service.get_all_payloads() == []


def test_load_payloads_metadata_skips_resource_with_missing_agent_template(
    service: PayloadsService,
    repo_service: RepositoryService,
    agent_templates_service: MagicMock,
):
    with patch("asyncio.create_task"):
        repo_service.create_file(
            content="payload",
            name="p.bin",
            data={
                "agent_template": "missing.label",
                "build_parameters": {},
                "payload_data": {},
            },
        )
    agent_templates_service.get_agent_template_by_label.side_effect = (
        AgentTemplateLabelNotFoundError(label="missing.label")
    )
    service.load_payloads_metadata()
    assert service.get_all_payloads() == []


# ---------------------------------------------------------------------------
# reserve_payload_id
# ---------------------------------------------------------------------------


def test_reserve_payload_id_returns_uuid(service: PayloadsService):
    pid = service.reserve_payload_id()
    assert isinstance(pid, uuid.UUID)


def test_reserve_payload_id_can_be_used_in_create(service: PayloadsService):
    # The reservation should be forwarded to the underlying repository service;
    # verify by checking it's tracked there
    pid = service.reserve_payload_id()
    # The reservation is stored inside the repository service's internal set
    assert str(pid) in service._repository_service._reserved_resource_ids


# ---------------------------------------------------------------------------
# get_payload_by_payload_id
# ---------------------------------------------------------------------------


def test_get_payload_by_payload_id_success(service: PayloadsService):
    p = _make_mock_payload()
    service._payloads[str(p.payload_id)] = p
    found = service.get_payload_by_payload_id(payload_id=str(p.payload_id))
    assert found is p


def test_get_payload_by_payload_id_not_found_raises(service: PayloadsService):
    with pytest.raises(PayloadNotFoundError):
        service.get_payload_by_payload_id(payload_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# get_all_payloads
# ---------------------------------------------------------------------------


def test_get_all_payloads_empty(service: PayloadsService):
    assert service.get_all_payloads() == []


def test_get_all_payloads_returns_all(service: PayloadsService):
    p1, p2 = _make_mock_payload(), _make_mock_payload()
    service._payloads[str(p1.payload_id)] = p1
    service._payloads[str(p2.payload_id)] = p2
    payloads = service.get_all_payloads()
    assert len(payloads) == 2


# ---------------------------------------------------------------------------
# delete_payload_by_payload_id
# ---------------------------------------------------------------------------


def test_delete_payload_both_exist(
    service: PayloadsService, repo_service: RepositoryService
):
    # Create a real repository file so resource_exists check passes
    with patch("asyncio.create_task"):
        resource = repo_service.create_file(content="payload", name="p.bin")
    payload_id = str(resource.resource_id)
    p = _make_mock_payload(payload_id=payload_id)
    service._payloads[payload_id] = p

    with patch("asyncio.create_task"):
        service.delete_payload_by_payload_id(payload_id=payload_id)

    assert payload_id not in service._payloads
    assert service.get_all_payloads() == []


def test_delete_payload_metadata_only_orphaned(
    service: PayloadsService,
):
    # Payload metadata exists but no repository resource; should clean up metadata
    p = _make_mock_payload()
    payload_id = str(p.payload_id)
    service._payloads[payload_id] = p
    # Repository service has no resource with that ID (it will raise RepositoryResourceNotFoundError)
    # delete_payload_by_payload_id handles this gracefully
    with patch("asyncio.create_task"):
        service.delete_payload_by_payload_id(payload_id=payload_id)
    assert payload_id not in service._payloads


def test_delete_payload_resource_only_orphaned(
    service: PayloadsService, repo_service: RepositoryService
):
    # A repository resource exists but no payload metadata; should clean up resource
    with patch("asyncio.create_task"):
        resource = repo_service.create_file(content="orphan", name="orphan.bin")
    payload_id = str(resource.resource_id)
    # No entry in _payloads
    with patch("asyncio.create_task"):
        service.delete_payload_by_payload_id(payload_id=payload_id)
    # Resource should be gone
    from consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions import (
        RepositoryResourceNotFoundError,
    )

    with pytest.raises(RepositoryResourceNotFoundError):
        repo_service.get_resource_by_resource_id(resource_id=payload_id)


def test_delete_payload_not_found_raises(service: PayloadsService):
    with pytest.raises(PayloadNotFoundError):
        with patch("asyncio.create_task"):
            service.delete_payload_by_payload_id(payload_id=str(uuid.uuid4()))
