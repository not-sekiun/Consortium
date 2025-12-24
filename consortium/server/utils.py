import functools
import inspect
import random
import types
import uuid
from collections.abc import Callable

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


def normalize_uuid(value: str | uuid.UUID) -> str:
    return str(value)


def log_and_propagate_error_on_service_method(func) -> Callable:
    @functools.wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except BaseConsortiumError as exc:
            self._logger.error("{}: {}", type(exc).__name__, exc)
            raise
        except Exception as exc:
            self._logger.opt(ansi=True, exception=exc).critical(
                "<white><RED><bold>Unhandled exception in {}.{}. {}: {}</></></>",
                type(self).__name__,
                func.__name__,
                type(exc).__name__,
                exc,
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except BaseConsortiumError as exc:
            self._logger.error("{}: {}", type(exc).__name__, exc)
            raise
        except Exception as exc:
            self._logger.opt(ansi=True, exception=exc).critical(
                "<white><RED><bold>Unhandled exception in {}.{}. {}: {}</></></>",
                type(self).__name__,
                func.__name__,
                type(exc).__name__,
                exc,
            )
            raise

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def construct_server_services_namespace_object(
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
