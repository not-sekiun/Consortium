from dataclasses import dataclass


@dataclass
class CommandInfo:
    name: str
    description: str
    group: str
    summary: str
