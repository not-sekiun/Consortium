import json
import pathlib
from enum import StrEnum

from pydantic import BaseModel

with open(
    pathlib.Path(__file__).parent.parent.parent.parent
    / "data"
    / "server"
    / "mitre_attack_data.json"
) as file:
    mitre_attack_data = json.load(file)


# Dynamically create StrEnum
MitreAttackTechniqueID = StrEnum(
    "MitreAttackTechniqueID",
    {tid.replace(".", "_"): tid for tid in mitre_attack_data.keys()},
)


class MitreAttackTechnique(BaseModel):
    mitre_attack_technique_id: MitreAttackTechniqueID
    name: str
    description: str
    tactics: list[str]
    url: str
    platforms: list[str]


def resolve_mitre_attack_technique_id(
    mitre_attack_technique_id: str,
) -> MitreAttackTechnique:
    data = mitre_attack_data[mitre_attack_technique_id]
    return MitreAttackTechnique(
        mitre_attack_technique_id=mitre_attack_technique_id,
        name=data["name"],
        description=data["description"],
        tactics=data["tactics"],
        url=data["url"],
        platforms=data["platforms"],
    )
