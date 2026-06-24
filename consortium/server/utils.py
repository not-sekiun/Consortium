import functools
import inspect
import random
import types
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)

if TYPE_CHECKING:
    from loguru import Logger


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


def construct_services_namespace_object(
    server_singletons: types.ModuleType,
) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        **{
            attr: getattr(server_singletons, attr)
            for attr in dir(server_singletons)
            if attr.endswith("_service") and not attr.startswith("_")
        },
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
