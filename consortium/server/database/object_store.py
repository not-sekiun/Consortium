from consortium.server.database.base_database import BaseDatabase
from consortium.server.database.base_database_entry import BaseDatabaseEntry


class ConsortiumObjectStore[T]:
    def __init__(self):
        self._consortium_objects: dict[str, T] = {}

    def add_object(self, object_id: str, consortium_object: T) -> None:
        self._consortium_objects[object_id] = consortium_object

    def remove_object(self, object_id: str) -> None:
        self._consortium_objects.pop(object_id)

    def get_object(self, object_id: str) -> T | None:
        return self._consortium_objects.get(object_id)

    def get_all_objects(self) -> list[T]:
        return list(self._consortium_objects.values())


class DatabaseBackedObjectStore[T: BaseDatabaseEntry](ConsortiumObjectStore[T]):
    def __init__(self, database: BaseDatabase[T]):
        super().__init__()
        self._database = database

    def add_object(self, object_id: str, consortium_object: T) -> None:
        super().add_object(object_id, consortium_object)
        self._database.add(consortium_object)

    def remove_object(self, object_id: str) -> None:
        consortium_object = self.get_object(object_id)
        if consortium_object is not None:
            self._database.remove(consortium_object)
        super().remove_object(object_id)
