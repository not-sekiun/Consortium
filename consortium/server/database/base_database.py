from abc import ABC, abstractmethod

from consortium.server.database.base_database_entry import BaseDatabaseEntry


class BaseDatabase[DatabaseEntry: BaseDatabaseEntry](ABC):
    @abstractmethod
    def get_by_id(self, database_entry_id: str) -> DatabaseEntry: ...

    @abstractmethod
    def get_all(self) -> list[DatabaseEntry]: ...
