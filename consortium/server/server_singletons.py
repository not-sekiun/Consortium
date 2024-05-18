from consortium.server.services.agent_generators_service import AgentGeneratorsService
from consortium.server.services.agent_profiles_service import AgentProfilesService
from consortium.server.services.agent_templates_service import AgentTemplatesService
from consortium.server.services.agents_service import AgentsService
from consortium.server.services.application_service import ApplicationService
from consortium.server.services.c2_types_service import C2TypesService
from consortium.server.services.event_hooks_service import EventHooksService
from consortium.server.services.listener_profiles_service import ListenerProfilesService
from consortium.server.services.listener_templates_service import (
    ListenerTemplatesService,
)
from consortium.server.services.listeners_service import ListenersService
from consortium.server.services.plugins_service import PluginsService
from consortium.server.services.user_accounts_service import UserAccountsService
from consortium.server.services.users_service import UsersService

application_service = ApplicationService()
event_hooks_service = EventHooksService()
c2_types_service = C2TypesService()
# Agent profiles service needs to be instantiated before the agent templates service
# because the agent templates service relies on the agent profiles service to retrieve
# agent profiles.
agent_profiles_service = AgentProfilesService()
agent_templates_service = AgentTemplatesService()
agent_generators_service = AgentGeneratorsService()
agents_service = AgentsService()
# Listener profiles service needs to be instantiated before the listener templates
# service because the listener templates service relies on the listener profiles
# service to retrieve listener profiles.
listener_profiles_service = ListenerProfilesService()
listener_templates_service = ListenerTemplatesService()
listeners_service = ListenersService()
user_accounts_service = UserAccountsService()
users_service = UsersService()
# Plugins service needs to be instantiated last so that the loaded plugins have access
# to all the other services.
plugins_service = PluginsService()
# The server instance is instantiated dynamically at start_server.py. The configuration
# values need to be passed into it over there before the instance can be assigned here.
server = None
