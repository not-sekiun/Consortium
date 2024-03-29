from consortium.server.services.agent_generator_templates_service import (
    AgentGeneratorTemplatesService,
)
from consortium.server.services.agents_service import AgentsService
from consortium.server.services.listener_templates_service import (
    ListenerTemplatesService,
)
from consortium.server.services.listeners_service import ListenersService
from consortium.server.services.user_accounts_service import UserAccountsService
from consortium.server.services.users_service import UsersService

agents_service = AgentsService()
listeners_service = ListenersService()
listener_templates_service = ListenerTemplatesService()
user_accounts_service = UserAccountsService()
users_service = UsersService()
agent_generator_templates_service = AgentGeneratorTemplatesService()
# The server instance is instantiated dynamically at start_server.py. The configuration
# values need to be passed into it over there before the instance can be assigned here.
server = None
