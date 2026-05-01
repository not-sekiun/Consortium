# import uuid
# from base_database import BaseDatabase
# from typing import TypeVar, Generic
#
# from consortium.server.exceptions.consortium_exceptions.database_exceptions import EntryNotFoundError
#
# Entry = TypeVar('Entry')
#
#
# class InMemoryDatabase(Generic[Entry], BaseDatabase[Entry]):
#     def __init__(self):
#         self.database: dict[str, Entry] = {}
#
#     def get_entry_by_id(self, entry_id: str) -> Entry:
#         try:
#             return self.database[entry_id]
#         except KeyError:
#             raise EntryNotFoundError(entry_id=entry_id)
#
#     def get_all_entries(self) -> Entry:
#         return list(self.database.values())
#
#         assigned_id = uuid.uuid4()
#         self.database[str(assigned_id)] = entry
#         return str(assigned_id)
#
#     def insert_entry(self, entry: Entry) -> str:
