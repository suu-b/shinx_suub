from pydantic import BaseModel

from shinx.shared.models.plan_node import PlanNode
from shinx.shared.models.db_metadata import DBMetadata

class QueryAnalysis(BaseModel):
    query: str
    dbMetdata: DBMetadata
    plan: PlanNode