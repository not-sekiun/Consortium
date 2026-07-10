from typing import TYPE_CHECKING

from consortium.server.models.repository_models import (
    PersistentArtifactDataModel,
    PersistentAssetDataModel,
    PersistentPayloadDataModel,
)
from consortium.server.services.agent_generators_service import AgentGeneratorsService
from consortium.server.services.agent_profiles_service import AgentProfilesService
from consortium.server.services.agent_templates_service import AgentTemplatesService
from consortium.server.services.agents_service import AgentsService
from consortium.server.services.artifacts_service import ArtifactsService
from consortium.server.services.assets_service import AssetsService
from consortium.server.services.authorization_service import AuthorizationService
from consortium.server.services.c2_types_service import C2TypesService
from consortium.server.services.consortium_paths_service import ConsortiumPathsService
from consortium.server.services.event_hooks_service import EventHooksService
from consortium.server.services.events_service import EventsService
from consortium.server.services.listener_profiles_service import ListenerProfilesService
from consortium.server.services.listener_templates_service import (
    ListenerTemplatesService,
)
from consortium.server.services.listeners_service import ListenersService
from consortium.server.services.logging_service import LoggingService
from consortium.server.services.payloads_service import PayloadsService
from consortium.server.services.plugins_service import PluginsService
from consortium.server.services.release_service import ReleaseService
from consortium.server.services.repository_service import RepositoryService
from consortium.server.services.user_accounts_service import UserAccountsService
from consortium.server.services.users_service import UsersService

if TYPE_CHECKING:
    from consortium.server.server import Server

# This service is first to instantiate because it registers a default sink pre-config
# such that every other service below it can log messges that are properly formatted
logging_service = LoggingService()


# This service is instantiated early because nearly every other service relies on it to
# retrieve important Consortium related directory paths. This service will abort
# server startup if certain critical paths do not exist and auto create other paths
# if they are missing.
consortium_paths_service = ConsortiumPathsService()

# The authorization service is instantiated immediately after consortium_paths_service
# so that role permissions are available as early as possible for the user accounts
# service
authorization_service = AuthorizationService(
    role_permissions_json_file=consortium_paths_service.role_permissions_json_file
)
user_accounts_service = UserAccountsService(
    user_accounts_json_file=consortium_paths_service.user_accounts_json_file,
    authorization_service=authorization_service,
)

# The event hooks, listener profiles, agent profiles, and plugins services need the
# server release service to be dependency injected into them when checking their '
# respective components for compatibility with the current server version. Therefore,
# we instantiate the server release service first.
release_service = ReleaseService(
    release_json_file=consortium_paths_service.release_json_file
)

# The event hooks, listeners, agent generators, agents, and users services need the
# events service to be dependency injected into them so we instantiate the events
# service first.
events_service = EventsService()
event_hooks_service = EventHooksService(
    events_service=events_service,
    release_service=release_service,
    event_hooks_directory=consortium_paths_service.event_hooks_directory,
    consortium_root=consortium_paths_service.consortium_root,
)

# Agent profiles service needs to be instantiated before the agent templates service
# because the agent templates service relies on the agent profiles service to retrieve
# agent profiles.
agent_profiles_service = AgentProfilesService(
    release_service=release_service,
    agents_directory=consortium_paths_service.agents_directory,
    consortium_root=consortium_paths_service.consortium_root,
)
agent_templates_service = AgentTemplatesService(
    agent_profiles_service=agent_profiles_service,
)
agent_generators_service = AgentGeneratorsService(
    agent_templates_service=agent_templates_service,
    events_service=events_service,
)

# Listener profiles service needs to be instantiated before the listener templates
# service because the listener templates service relies on the listener profiles
# service to retrieve listener profiles.
listener_profiles_service = ListenerProfilesService(
    release_service=release_service,
    listeners_directory=consortium_paths_service.listeners_directory,
    consortium_root=consortium_paths_service.consortium_root,
)
listener_templates_service = ListenerTemplatesService(
    listener_profiles_service=listener_profiles_service,
)
listeners_service = ListenersService(
    listener_templates_service=listener_templates_service,
    events_service=events_service,
)

# C2 types service needs to be instantiated after the listener profiles service and
# agent profiles service because it relies on both of them to retrieve listener and
# agent type information.
c2_types_service = C2TypesService(
    listener_profiles_service=listener_profiles_service,
    agent_profiles_service=agent_profiles_service,
)

agents_service = AgentsService(
    events_service=events_service,
)

# The payloads service relies on the _agent_templates_service to check that the metadata
# of loaded payloads is correct
payloads_service = PayloadsService(
    events_service=events_service,
    repository_service=RepositoryService(
        repository_directory_path=consortium_paths_service.payloads_directory,
        data_model=PersistentPayloadDataModel,
    ),
    agent_templates_service=agent_templates_service,
)

# The assets service relies on the user accounts service to resolve an uploading user
# account ID into a stored user account reference, and the artifacts service relies on
# the agents service to resolve a producing agent ID into a stored agent reference.
assets_service = AssetsService(
    events_service=events_service,
    repository_service=RepositoryService(
        repository_directory_path=consortium_paths_service.assets_directory,
        data_model=PersistentAssetDataModel,
    ),
    user_accounts_service=user_accounts_service,
)
artifacts_service = ArtifactsService(
    events_service=events_service,
    repository_service=RepositoryService(
        repository_directory_path=consortium_paths_service.artifacts_directory,
        data_model=PersistentArtifactDataModel,
    ),
    agents_service=agents_service,
)
users_service = UsersService(events_service=events_service)

# The plugins service needs to be instantiated last so that the loaded plugins have
# access to all the other services.
plugins_service = PluginsService(
    release_service=release_service,
    plugins_directory=consortium_paths_service.plugins_directory,
    consortium_root=consortium_paths_service.consortium_root,
)

# The server instance is instantiated dynamically at `start_server.py`. The configuration
# values need to be passed into it over there before the instance can be assigned here.
server: Server | None = None
