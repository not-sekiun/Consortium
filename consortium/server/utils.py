import functools
import inspect
import random
import types
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)

if TYPE_CHECKING:
    from loguru import Logger

    from consortium.server.services.agent_generators_service import (
        AgentGeneratorsService,
    )
    from consortium.server.services.agent_profiles_service import AgentProfilesService
    from consortium.server.services.agent_templates_service import AgentTemplatesService
    from consortium.server.services.agents_service import AgentsService
    from consortium.server.services.authorization_service import AuthorizationService
    from consortium.server.services.c2_types_service import C2TypesService
    from consortium.server.services.consortium_paths_service import (
        ConsortiumPathsService,
    )
    from consortium.server.services.event_hooks_service import EventHooksService
    from consortium.server.services.events_service import EventsService
    from consortium.server.services.listener_profiles_service import (
        ListenerProfilesService,
    )
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


def normalize_uuid(value: str | uuid.UUID) -> str:
    return str(value)


def log_and_propagate_error_on_service_method(func) -> Callable:
    def _log_service_method_error(
        logger: Logger, instance: Any, func_name: str, exc: Exception
    ) -> None:
        if isinstance(exc, BaseConsortiumError):
            logger.error(
                "Error in `{}.{}`. {}: {}",
                type(instance).__name__,
                func_name,
                type(exc).__name__,
                exc,
            )
        else:
            logger.opt(ansi=True, exception=exc).critical(
                "<white><RED><bold>Unhandled exception in `{}.{}`. {}: {}</></></>",
                type(instance).__name__,
                func_name,
                type(exc).__name__,
                exc,
            )

    @functools.wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as exc:
            _log_service_method_error(self._logger, self, func.__name__, exc)
            raise

    @functools.wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as exc:
            _log_service_method_error(self._logger, self, func.__name__, exc)
            raise

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


@dataclass(frozen=True)
class Services:
    logging_service: LoggingService | None
    authorization_service: AuthorizationService
    consortium_paths_service: ConsortiumPathsService
    release_service: ReleaseService
    events_service: EventsService
    event_hooks_service: EventHooksService
    agent_profiles_service: AgentProfilesService
    agent_templates_service: AgentTemplatesService
    agent_generators_service: AgentGeneratorsService
    listener_profiles_service: ListenerProfilesService
    listener_templates_service: ListenerTemplatesService
    listeners_service: ListenersService
    c2_types_service: C2TypesService
    agents_service: AgentsService
    payloads_service: PayloadsService
    assets_service: RepositoryService
    artifacts_service: RepositoryService
    user_accounts_service: UserAccountsService
    users_service: UsersService
    plugins_service: PluginsService


def construct_services_dataclass(
    server_singletons: types.ModuleType,
) -> Services:
    return Services(
        authorization_service=server_singletons.authorization_service,
        logging_service=server_singletons.logging_service,
        consortium_paths_service=server_singletons.consortium_paths_service,
        release_service=server_singletons.release_service,
        events_service=server_singletons.events_service,
        event_hooks_service=server_singletons.event_hooks_service,
        agent_profiles_service=server_singletons.agent_profiles_service,
        agent_templates_service=server_singletons.agent_templates_service,
        agent_generators_service=server_singletons.agent_generators_service,
        listener_profiles_service=server_singletons.listener_profiles_service,
        listener_templates_service=server_singletons.listener_templates_service,
        listeners_service=server_singletons.listeners_service,
        c2_types_service=server_singletons.c2_types_service,
        agents_service=server_singletons.agents_service,
        payloads_service=server_singletons.payloads_service,
        assets_service=server_singletons.assets_service,
        artifacts_service=server_singletons.artifacts_service,
        user_accounts_service=server_singletons.user_accounts_service,
        users_service=server_singletons.users_service,
        plugins_service=server_singletons.plugins_service,
    )


def generate_random_human_readable_name():
    colors = [
        "AMBER",
        "AMETHYST",
        "BERYL",
        "DIAMOND",
        "EMERALD",
        "JADE",
        "OBSIDIAN",
        "ONYX",
        "OPAL",
        "PERIDOT",
        "QUARTZ",
        "RUBY",
        "SAPPHIRE",
        "TOPAZ",
        "ZIRCON",
        "APRICOT",
        "CERISE",
        "CHERRY",
        "CORAL",
        "HEATHER",
        "INDIGO",
        "IRIS",
        "LAVENDER",
        "LILAC",
        "MARIGOLD",
        "OLIVE",
        "ORCHID",
        "PEACH",
        "ROSE",
        "SAFFRON",
        "SAGE",
        "AZURE",
        "CANARY",
        "CERULEAN",
        "CYAN",
        "FUCHSIA",
        "MAGENTA",
        "SCARLET",
        "TURQUOISE",
        "VERMILION",
        "VIOLET",
        "BRONZE",
        "COPPER",
        "GOLD",
        "IRON",
        "NICKEL",
        "PLATINUM",
        "SILVER",
        "STEEL",
        "TITANIUM",
    ]
    celestials = [
        "ALTAIR",
        "ANTARES",
        "APUS",
        "AQUILA",
        "ARA",
        "ARGO",
        "ARIES",
        "AURIGA",
        "CANCER",
        "CANIS",
        "CARINA",
        "CETUS",
        "CHARA",
        "COLUMBA",
        "CORVUS",
        "CRATER",
        "CRUX",
        "CYGNUS",
        "DELPHINUS",
        "DORADO",
        "DRACO",
        "FORNAX",
        "GEMINI",
        "GRUS",
        "HYDRA",
        "INDUS",
        "LEO",
        "LEPUS",
        "LIBRA",
        "LUPUS",
        "LYRA",
        "MENSA",
        "NORMA",
        "ORION",
        "PAVO",
        "PEGASUS",
        "PERSEUS",
        "PHOENIX",
        "PICTOR",
        "PISCES",
        "PUPPIS",
        "PYXIS",
        "SAGITTA",
        "SERPENS",
        "SIRIUS",
        "TAURUS",
        "TUCANA",
        "URSA",
        "VELA",
        "VIRGO",
    ]
    return f"{random.choice(colors).upper()} {random.choice(celestials).upper()}"
