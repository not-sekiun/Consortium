from abc import ABC, abstractmethod
from typing import Self

from pydantic import BaseModel


class BaseDatabaseEntry[T: BaseModel](ABC):
    database_model: T

    @abstractmethod
    def resolve_id(self) -> str: ...

    @abstractmethod
    def to_database_model(self) -> T: ...

    @classmethod
    @abstractmethod
    def from_database_model(cls, model: T) -> Self: ...
