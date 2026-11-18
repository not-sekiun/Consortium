from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


class AliasesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    local_aliases: dict[str, str]
    global_aliases: dict[str, str]


@dataclass
class Alias:
    command: str
    is_global: bool
