from sqlalchemy import Engine, Table

from consortium.server.database.base_database import BaseDatabase


class SQLDatabase[DatabaseEntry](BaseDatabase):
    def __init__(self, engine: Engine, table: Table):
        self._engine = engine
        self._table = table

    def get_entry_by_id(self, database_entry_id: str) -> DatabaseEntry | None:
        pass

    def get_all_entries(self) -> list[DatabaseEntry]:
        pass

    def add_entry(self, database_entry: DatabaseEntry) -> None:
        pass

    def remove_entry(self, database_entry: DatabaseEntry) -> None:
        pass
