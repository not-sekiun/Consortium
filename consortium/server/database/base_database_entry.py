from abc import ABC, abstractmethod
from typing import Self

from pydantic import BaseModel


class BaseDatabaseEntry[DatabaseModel: BaseModel](ABC):
    database_model: DatabaseModel

    @abstractmethod
    def resolve_id(self) -> str: ...

    @abstractmethod
    def to_database_model(self) -> DatabaseModel: ...

    @classmethod
    @abstractmethod
    def from_database_model(cls, model: DatabaseModel) -> Self: ...
