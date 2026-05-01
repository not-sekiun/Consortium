# from abc import ABC, abstractmethod
# from typing import Generic, TypeVar
#
# Entry = TypeVar("Entry")
#
#
# class BaseDatabase(ABC, Generic[Entry]):
#     @abstractmethod
#     def get_entry_by_id(self, entry_id: str) -> Entry: ...
#
#     @abstractmethod
#     def get_all_entries(self) -> list[Entry]: ...
#
#     @abstractmethod
#     def insert_entry(self, entry: Entry) -> str: ...
