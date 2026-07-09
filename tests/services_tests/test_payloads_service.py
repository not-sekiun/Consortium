import pathlib
import uuid
from unittest.mock import MagicMock, patch

import pytest

from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.framework.event_hooks import EventType
from consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions import (
    AgentTemplateLabelNotFoundError,
)
from consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions import (
    PayloadNotFoundError,
)
from consortium.server.objects.payload_objects import Payload
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


def _create_payload_resource(
    repo_service: RepositoryService,
    *,
    label: str = "test.label",
    name: str = "Test Template",
    build_parameters: dict | None = None,
    payload_data: dict | None = None,
):
    # A payload is "just" a repository resource whose `data` field carries the payload
    # metadata (an immutable point-in-time reference to the generating agent template,
    # the build parameters and arbitrary payload data). This mirrors what the payloads
    # service persists via `_build_payload_resource_data`.
    return repo_service.create_file(
        content="payload",
        name="p.bin",
        data={
            "agent_template": {"label": label, "name": name},
            "build_parameters": build_parameters
            if build_parameters is not None
            else {},
            "payload_data": payload_data if payload_data is not None else {},
        },
    )


def _make_agent_template(
    label: str = "test.label", name: str = "Test Template"
) -> MagicMock:
    agent_template = MagicMock(spec=BaseAgentTemplate)
    agent_template.label = label
    agent_template.name = name
    agent_template.agent_type = MagicMock()
    return agent_template


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
# create_payload_file
# ---------------------------------------------------------------------------


def test_create_payload_file_persists_reference_and_metadata(
    service: PayloadsService, agent_templates_service: MagicMock
):
    agent_template = _make_agent_template()
    agent_templates_service.get_agent_template_by_agent_template_id.return_value = (
        agent_template
    )

    with patch("asyncio.create_task"):
        payload = service.create_payload_file(
            agent_template_id="ignored-by-mock",
            build_parameters={"foo": "bar"},
            content="payload-bytes",
            payload_data={"baz": 1},
        )

    # The generating agent template is stored as an immutable point-in-time reference
    # (label and name only), not its ID.
    assert payload.data["agent_template"] == {
        "label": "test.label",
        "name": "Test Template",
    }
    assert payload.data["build_parameters"] == {"foo": "bar"}
    assert payload.data["payload_data"] == {"baz": 1}

    # The payload is derived from the repository, so it is immediately retrievable.
    assert len(service.get_all_payloads()) == 1
    fetched = service.get_payload_by_payload_id(payload_id=str(payload.resource_id))
    assert fetched.resource_id == payload.resource_id


def test_create_payload_file_emits_payload_created_event(
    service: PayloadsService,
    events_service: MagicMock,
    agent_templates_service: MagicMock,
):
    agent_templates_service.get_agent_template_by_agent_template_id.return_value = (
        _make_agent_template()
    )
    with patch("asyncio.create_task"):
        service.create_payload_file(
            agent_template_id="ignored-by-mock",
            build_parameters={},
            content="payload-bytes",
        )
    events_service.trigger_event.assert_called_once()
    assert (
        events_service.trigger_event.call_args.kwargs["event_type"]
        == EventType.PAYLOAD_CREATED
    )


# ---------------------------------------------------------------------------
# get_payload_by_payload_id
# ---------------------------------------------------------------------------


def test_get_payload_by_payload_id_success(
    service: PayloadsService, repo_service: RepositoryService
):
    resource = _create_payload_resource(
        repo_service, build_parameters={"foo": "bar"}, payload_data={"baz": 1}
    )
    payload = service.get_payload_by_payload_id(payload_id=str(resource.resource_id))
    assert isinstance(payload, Payload)
    assert payload.resource_id == resource.resource_id
    assert payload.data["build_parameters"] == {"foo": "bar"}
    assert payload.data["payload_data"] == {"baz": 1}


def test_get_payload_by_payload_id_not_found_raises(service: PayloadsService):
    with pytest.raises(PayloadNotFoundError):
        service.get_payload_by_payload_id(payload_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# get_all_payloads
# ---------------------------------------------------------------------------


def test_get_all_payloads_empty(service: PayloadsService):
    assert service.get_all_payloads() == []


def test_get_all_payloads_returns_all(
    service: PayloadsService, repo_service: RepositoryService
):
    r1 = _create_payload_resource(repo_service)
    r2 = _create_payload_resource(repo_service)
    payloads = service.get_all_payloads()
    assert len(payloads) == 2
    assert {str(p.resource_id) for p in payloads} == {
        str(r1.resource_id),
        str(r2.resource_id),
    }


# ---------------------------------------------------------------------------
# resolved_agent_template (Payload wrapper resolution)
# ---------------------------------------------------------------------------


def test_payload_resolves_live_agent_template(
    service: PayloadsService,
    repo_service: RepositoryService,
    agent_templates_service: MagicMock,
):
    _create_payload_resource(repo_service, label="test.label")
    sentinel_template = MagicMock()
    agent_templates_service.get_agent_template_by_label.return_value = sentinel_template

    payload = service.get_all_payloads()[0]
    assert payload.resolved_agent_template is sentinel_template
    agent_templates_service.get_agent_template_by_label.assert_called_once_with(
        label="test.label"
    )


def test_payload_resolution_returns_none_when_agent_template_deleted(
    service: PayloadsService,
    repo_service: RepositoryService,
    agent_templates_service: MagicMock,
):
    _create_payload_resource(repo_service, label="missing.label")
    agent_templates_service.get_agent_template_by_label.side_effect = (
        AgentTemplateLabelNotFoundError(label="missing.label")
    )
    payload = service.get_all_payloads()[0]
    assert payload.resolved_agent_template is None


# ---------------------------------------------------------------------------
# delete_payload_by_payload_id
# ---------------------------------------------------------------------------


def test_delete_payload_removes_resource_and_emits_event(
    service: PayloadsService,
    repo_service: RepositoryService,
    events_service: MagicMock,
    agent_templates_service: MagicMock,
):
    agent_templates_service.get_agent_template_by_label.side_effect = (
        AgentTemplateLabelNotFoundError(label="test.label")
    )
    resource = _create_payload_resource(repo_service)
    payload_id = str(resource.resource_id)

    with patch("asyncio.create_task"):
        service.delete_payload_by_payload_id(payload_id=payload_id)

    assert service.get_all_payloads() == []
    with pytest.raises(PayloadNotFoundError):
        service.get_payload_by_payload_id(payload_id=payload_id)
    events_service.trigger_event.assert_called_once()
    assert (
        events_service.trigger_event.call_args.kwargs["event_type"]
        == EventType.PAYLOAD_DELETED
    )


def test_delete_payload_not_found_raises(service: PayloadsService):
    with pytest.raises(PayloadNotFoundError):
        with patch("asyncio.create_task"):
            service.delete_payload_by_payload_id(payload_id=str(uuid.uuid4()))


def test_delete_payload_not_found_leaves_repository_untouched(
    service: PayloadsService, repo_service: RepositoryService
):
    # Deleting an unknown payload ID must not affect existing resources.
    resource = _create_payload_resource(repo_service)
    with pytest.raises(PayloadNotFoundError):
        with patch("asyncio.create_task"):
            service.delete_payload_by_payload_id(payload_id=str(uuid.uuid4()))
    # The unrelated resource still exists.
    assert (
        repo_service.get_resource_by_resource_id(
            resource_id=str(resource.resource_id)
        ).resource_id
        == resource.resource_id
    )
