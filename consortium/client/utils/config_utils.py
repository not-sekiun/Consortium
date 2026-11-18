import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from consortium.client.exceptions.config_exceptions import ConfigLoadError
from consortium.client.models.alias_models import Alias, AliasesConfig
from consortium.client.utils.formatter_utils import format_validation_error


def load_config_model_from_json_file[T: BaseModel](
    path: str | Path,
    model: type[T],
    description: str,
) -> T:
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise ConfigLoadError(
            f"Could not find the {description} file at '{path}'."
        ) from exc
    except IsADirectoryError as exc:
        raise ConfigLoadError(
            f"The {description} path '{path}' is a directory, not a file."
        ) from exc
    except PermissionError as exc:
        raise ConfigLoadError(
            f"Permission denied when attempting to read the {description} file at '{path}'."
        ) from exc
    except UnicodeDecodeError as exc:
        raise ConfigLoadError(
            f"The {description} file '{path}' does not contain valid UTF-8 text."
        ) from exc
    except json.JSONDecodeError as exc:
        raise ConfigLoadError(
            f"The {description} file '{path}' does not contain valid JSON data."
        ) from exc
    except OSError as exc:
        raise ConfigLoadError(
            f"Could not read the {description} file at '{path}': {exc}"
        ) from exc

    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ConfigLoadError(
            f"The {description} file '{path}' does not adhere to the expected "
            f"{description} format:\n{format_validation_error(exc)}"
        ) from exc


def load_aliases_from_json_file(path: str | Path) -> dict[str, Alias]:
    config = load_config_model_from_json_file(
        path=path,
        model=AliasesConfig,
        description="alias configuration",
    )
    aliases = {
        name: Alias(command=command, is_global=False)
        for name, command in config.local_aliases.items()
    }
    aliases.update(
        (name, Alias(command=command, is_global=True))
        for name, command in config.global_aliases.items()
    )
    return aliases
