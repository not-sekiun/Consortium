import random
import secrets
import string
from typing import Literal


def random_number(start: int, end: int) -> int:
    return random.randint(start, end)


def random_port(exclude_privileged: bool = True) -> int:
    if exclude_privileged:
        return random_number(start=1024, end=65535)

    return random_number(start=0, end=65535)


def random_ascii(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


def random_urlsafe(length: int = 16) -> str:
    return secrets.token_urlsafe(length)


def random_alphanumeric(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def random_hex(length: int = 16) -> str:
    return secrets.token_hex(length // 2 + length % 2)[:length]


def random_bytes(length: int = 16) -> bytes:
    return secrets.token_bytes(length)


def random_name(
    spacing: Literal["whitespace", "underscore", "dash", "dot"] = "whitespace",
    formatting: Literal["upper", "lower", "capitalized"] = "upper",
) -> str:
    spacing_to_char_map = {
        "whitespace": " ",
        "underscore": "_",
        "dash": "-",
        "dot": ".",
    }
    formatting_to_str_format_func_map = {
        "upper": lambda x: x.upper(),
        "lower": lambda x: x.lower(),
        "capitalized": lambda x: x.capitalize(),
    }
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

    format_func = formatting_to_str_format_func_map.get(formatting, str.upper)
    rand_color = format_func(random.choice(colors))
    rand_celestial = format_func(random.choice(celestials))
    spacing = spacing_to_char_map.get(spacing, " ")

    return f"{rand_color}{spacing}{rand_celestial}"
