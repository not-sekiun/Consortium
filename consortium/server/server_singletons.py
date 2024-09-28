from consortium.server.services.agent_generators_service import AgentGeneratorsService
from consortium.server.services.agent_profiles_service import AgentProfilesService
from consortium.server.services.agent_templates_service import AgentTemplatesService
from consortium.server.services.agents_service import AgentsService
from consortium.server.services.application_service import ApplicationService
from consortium.server.services.c2_types_service import C2TypesService
from consortium.server.services.event_hooks_service import EventHooksService
from consortium.server.services.events_service import EventsService
from consortium.server.services.listener_profiles_service import ListenerProfilesService
from consortium.server.services.listener_templates_service import (
    ListenerTemplatesService,
)
from consortium.server.services.listeners_service import ListenersService
from consortium.server.services.plugins_service import PluginsService
from consortium.server.services.user_accounts_service import UserAccountsService
from consortium.server.services.users_service import UsersService

# The event hooks, listeners, agent generators, agents, and users services need the
# events service to be dependency injected into them so we instantiate the events
# service first.
events_service = EventsService()
event_hooks_service = EventHooksService(events_service=events_service)

# Agent profiles service needs to be instantiated before the agent templates service
# because the agent templates service relies on the agent profiles service to retrieve
# agent profiles.
agent_profiles_service = AgentProfilesService()
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
listener_profiles_service = ListenerProfilesService()
listener_templates_service = ListenerTemplatesService(
    listener_profiles_service=listener_profiles_service,
)
listeners_service = ListenersService(
    listener_templates_service=listener_templates_service,
    events_service=events_service,
)

c2_types_service = C2TypesService(
    listener_profiles_service=listener_profiles_service,
    agent_profiles_service=agent_profiles_service,
)

agents_service = AgentsService(
    events_service=events_service,
)

# These services are instantiated independent of other services.
application_service = ApplicationService()
user_accounts_service = UserAccountsService()
users_service = UsersService()
# The plugins service needs to be instantiated last so that the loaded plugins have
# access to all the other services.
plugins_service = PluginsService()
# The server instance is instantiated dynamically at start_server.py. The configuration
# values need to be passed into it over there before the instance can be assigned here.
server = None
