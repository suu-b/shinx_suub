from pydantic import BaseModel, Field

class Extension(BaseModel):
    name: str
    default_version: str | None = None
    installed_version: str | None = None
    comment: str | None = None

class Column(BaseModel):
    name: str
    data_type: str
    is_nullable: str
    column_default: str

class Constraint(BaseModel):
    name: str
    type: str
    columns: list[str] = Field(default_factory=list)

    referenced_table: str | None = None
    referenced_columns: list[str] = Field(default_factory=list)

    definition: str | None = None
    is_deferrable: bool | None = None
    initially_deferred: bool | None = None
    is_validated: bool | None = None
    on_update: str | None = None
    on_delete: str | None = None

class Index(BaseModel):
    name: str
    indexdef: str

class TableMetaData(BaseModel):
    name: str
    schema_name: str
    columns: list[Column]
    constraints: list[Constraint]
    indexes: list[Index]

class ViewColumn(BaseModel):
    column_name: str
    ordinal_position: int
    data_type: str
    is_nullable: str

class View(BaseModel):
    name: str
    schema_name: str
    owner: str | None = None
    definition: str | None = None
    is_updatable: bool | None = None
    is_insertable_into: bool | None = None
    is_trigger_updatable: bool | None = None
    is_trigger_deletable: bool | None = None
    is_trigger_insertable: bool | None = None
    is_materialized: bool | None = None
    description: str | None = None
    columns: list[ViewColumn] = []

class DBMetadata(BaseModel):
    version: str
    extensions: list[Extension]
    tables: list[TableMetaData]
    views: list[View]