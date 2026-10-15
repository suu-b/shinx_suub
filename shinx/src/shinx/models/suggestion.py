from enum import Enum
from pydantic import BaseModel, Field


class SuggestionType(str, Enum):
    INDEX_CREATION = "INDEX_CREATION"
    INDEX_DROP = "INDEX_DROP"
    QUERY_REWRITE = "QUERY_REWRITE"
    SCHEMA_CHANGE = "SCHEMA_CHANGE"
    CONFIGURATION = "CONFIGURATION"


class ImpactLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Suggestion(BaseModel):
    title: str = Field(description="Concise description of the suggestion, e.g. 'Add composite index on members(status, created_at)'")
    type: SuggestionType = Field(description="The category of the optimization suggestion")
    impact: ImpactLevel = Field(description="Estimated impact on performance (HIGH, MEDIUM, LOW)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    explanation: str = Field(description="Detailed technical reasoning why this improves query performance")
    suggested_sql: str | None = Field(default=None, description="Concrete SQL statement (DDL for index/table or rewritten SQL query)")
    trade_offs: str | None = Field(default=None, description="Potential trade-offs or risks (e.g. write performance overhead, disk space)")


class OptimizationReport(BaseModel):
    query: str = Field(description="The original user SQL query analyzed")
    bottleneck_identified: str = Field(description="Root cause of query inefficiency based on execution plan and schema")
    suggestions: list[Suggestion] = Field(default_factory=list, description="Ordered list of recommended optimization actions")
    database_engine: str | None = Field(default=None, description="Database dialect and version if detected")
