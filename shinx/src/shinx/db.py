from abc import ABC, abstractmethod

from shinx.models.db_metadata import (DBMetadata, TableMetaData, Column, Constraint, View, Index)
from shinx.models.plan_node import PlanNode

class DatabaseAdapter(ABC):
    def __init__(self):
        self._connection = None

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def get_database_structure(self) -> DBMetadata:
        ...

    @abstractmethod
    def explain(self, query) -> PlanNode:
        ...

    @abstractmethod
    def _get_database_info(self) -> dict:
        ...

    @abstractmethod
    def _get_tables(self) -> list[TableMetaData]:
        ...

    @abstractmethod
    def _get_columns(self, schema, table) -> list[Column]:
        ...

    @abstractmethod
    def _get_constraints(self, schema, table) -> list[Constraint]:
        ...

    @abstractmethod
    def _get_indexes(self, schema, table) -> list[Index]:
        ...

    @abstractmethod
    def _get_views(self) -> list[View]:
        ...

    @abstractmethod
    def get_table_metadata(self, table_name: str, schema_name: str = "public") -> TableMetaData | None:
        ...

    @abstractmethod
    def list_table_names(self, schema_name: str = "public") -> list[str]:
        ...

    @abstractmethod
    def get_database_info(self) -> dict:
        ...

    @abstractmethod
    def get_table_stats(self, table_name: str, schema_name: str = "public") -> dict:
        ...
