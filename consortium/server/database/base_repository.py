# from abc import abstractmethod, ABC
#
# from consortium.server.database.base_database import BaseDatabase
#
#
# class BaseRepository(ABC):
#     def __init__(self, database: BaseDatabase):
#         self._database  = database
#         self._entity_map = {}
#
#     def get_all_entities(self) -> list:
#         return self._database.get_all_entries()
#
#     def _convert_entity_to_entry(self):
