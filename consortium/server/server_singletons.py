from consortium.server.services.agent_generator_templates_service import (
    AgentGeneratorTemplatesService,
)
from consortium.server.services.agent_generators_service import AgentGeneratorsService
from consortium.server.services.agents_service import AgentsService
from consortium.server.services.listener_templates_service import (
    ListenerTemplatesService,
)
from consortium.server.services.listeners_service import ListenersService
from consortium.server.services.user_accounts_service import UserAccountsService
from consortium.server.services.users_service import UsersService

agent_generator_templates_service = AgentGeneratorTemplatesService()
listener_templates_service = ListenerTemplatesService()
user_accounts_service = UserAccountsService()
listeners_service = ListenersService()
agent_generators_service = AgentGeneratorsService()
users_service = UsersService()
agents_service = AgentsService()
# The server instance is instantiated dynamically at start_server.py. The configuration
# values need to be passed into it over there before the instance can be assigned here.
server = None
