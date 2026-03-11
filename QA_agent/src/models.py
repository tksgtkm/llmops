from pydantic import BaseModel, Field
from qdrant_client.models import ScoredPoint

class SearchOutput(BaseModel):
    file_name: str = Field(description="The file name")
    content: str = Field(description="The content of the file")

    @classmethod
    def from_hit(cls, hit: dict) -> "SearchOutput":
        return cls(
            file_name=hit["_source"]["file_name"], content=hit["_source"]["content"]
        )
    
    @classmethod
    def from_point(cls, point: ScoredPoint) -> "SearchOutput":
        if point.payload is None:
            raise ValueError("Payload is None")
        return cls(
            file_name=point.payload["file_name"], content=point.payload["content"]
        )