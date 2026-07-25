import asyncio
import functools
import inspect
import operator
import random
import types
import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, RootModel, create_model

from consortium.framework._core.framework_exceptions.base_framework_exception import (
    BaseFrameworkError,
)
from consortium.server.exceptions.object_exceptions.base_object_exception import (
    BaseObjectError,
)
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)

if TYPE_CHECKING:
    from fastapi.routing import APIRoute
    from loguru import Logger

    from consortium.server.exceptions.api_exceptions.base_api_exception import (
        BaseAPIError,
    )
    from consortium.server.services.agent_generators_service import (
        AgentGeneratorsService,
    )
    from consortium.server.services.agent_profiles_service import AgentProfilesService
    from consortium.server.services.agent_templates_service import AgentTemplatesService
    from consortium.server.services.agents_service import AgentsService
    from consortium.server.services.artifacts_service import ArtifactsService
    from consortium.server.services.assets_service import AssetsService
    from consortium.server.services.authorization_service import AuthorizationService
    from consortium.server.services.c2_types_service import C2TypesService
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
    from consortium.server.services.paths_service import (
        PathsService,
    )
    from consortium.server.services.payloads_service import PayloadsService
    from consortium.server.services.plugins_service import PluginsService
    from consortium.server.services.release_service import ReleaseService
    from consortium.server.services.user_accounts_service import UserAccountsService
    from consortium.server.services.users_service import UsersService


def use_route_name_as_operation_id(route: APIRoute) -> str:
    # FastAPI's default operationId is `{route.name}_{path}_{method}`, which makes
    # OpenAPI client generators emit long, mangled method names like
    # `get_all_agents_api_agents_all_get`. Returning just the route name yields clean
    # client methods (`get_all_agents`). This is passed to FastAPI via
    # `generate_unique_id_function`. Route names must be unique across the whole app:
    # decorator routes use their (unique) handler function name, and the repository
    # factory routes set an explicit per-router `name=` (for example "Get All Assets")
    # for exactly this reason.
    return route.name


# Cache of the union response models created by `create_union_response_model`, keyed by
# the model name. A given union (for example an invalid-UUID or unprocessable-entity 422)
# is declared on many endpoints, so caching guarantees a single class per name. Two
# distinct classes sharing a name would make the OpenAPI schema mangle both names, which
# is exactly the ugliness this helper exists to avoid.
_union_response_models: dict[str, type[BaseModel]] = {}


def create_union_response_model(
    name: str,
    exceptions: tuple[BaseAPIError, ...],
) -> type[BaseModel]:
    # Build a single named model for an error response whose body may be one of several
    # error shapes. Passing a bare union (`A | B`) as a route's response `model` leaves
    # the union anonymous, so OpenAPI client generators invent ugly names like
    # `Response404GetAgentTasksByAgentIdAndTaskId`. Wrapping the union in a named
    # RootModel gives the schema a stable component name (`name`) that generators reuse
    # verbatim, and endpoints sharing the same union share the one component.
    if name in _union_response_models:
        return _union_response_models[name]

    # `to_pydantic_model()` returns the cached, named pydantic model for each API
    # exception, so the union is over already-named components.
    error_models = tuple(exception.to_pydantic_model() for exception in exceptions)
    union_type = functools.reduce(operator.or_, error_models)
    union_response_model = create_model(name, __base__=RootModel[union_type])

    _union_response_models[name] = union_response_model
    return union_response_model


def normalize_uuid(value: str | uuid.UUID) -> str:
    return str(value)


def utc_now() -> datetime:
    # Timezone-aware UTC timestamp. Use this everywhere a datetime is persisted or
    # serialized so stored and emitted timestamps carry an explicit UTC offset instead
    # of an ambiguous naive local time. A naive datetime.now() is only correct when the
    # producer and consumer share a timezone; utc_now removes that hidden assumption.
    # Displaying in local time stays the consumer's job (the client already converts).
    return datetime.now(UTC)


def log_and_propagate_error_on_service_method(func) -> Callable:
    def _log_service_method_error(
        logger: Logger, instance: Any, func_name: str, exc: Exception
    ) -> None:
        if isinstance(exc, (BaseServiceError, BaseFrameworkError, BaseObjectError)):
            logger.error(
                "Error in `{}.{}`. {}: {}",
                type(instance).__name__,
                func_name,
                type(exc).__name__,
                exc,
            )
        else:
            logger.opt(colors=True, exception=exc).critical(
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
    paths_service: PathsService
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
    assets_service: AssetsService
    artifacts_service: ArtifactsService
    user_accounts_service: UserAccountsService
    users_service: UsersService
    plugins_service: PluginsService


def construct_services_dataclass(
    server_singletons: types.ModuleType,
) -> Services:
    return Services(
        authorization_service=server_singletons.authorization_service,
        logging_service=server_singletons.logging_service,
        paths_service=server_singletons.paths_service,
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


MAX_EVENT_LOG_LIMIT = 1000


# Hard server-side ceiling on how many event log entries a single request may return.
# Event logs are held in memory, so this bounds response size and memory use regardless
# of what a client asks for. Requests above this value are clamped down to it rather than
# rejected, so callers that pass a large number to mean "everything" still succeed.
def clamp_event_log_limit(limit: int) -> int:
    # Callers still validate the lower bound (gt=0) at the query layer; this only caps
    # the upper bound before the value reaches the event log.
    return min(limit, MAX_EVENT_LOG_LIMIT)


_background_tasks = set()


# Running fire and forget background tasks safely. The _coroutine set is needed since
# tasks are only held onto by a weak reference and may be GCed at any time.
def run_async_background_task(coroutine: Coroutine) -> None:
    task = asyncio.create_task(coroutine)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
