from consortium.server.database.base_database import BaseDatabase


class InMemoryDatabase[DatabaseEntry](BaseDatabase):
    def __init__(self):
        self._database: dict[str, DatabaseEntry] = {}

    def get_by_id(self, database_entry_id: str) -> DatabaseEntry:
        return self._database.get(database_entry_id)

    def get_all(self) -> list[DatabaseEntry]:
        return list(self._database.values())
