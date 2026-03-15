from langchain.tools import tool
from openai import OpenAI
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from src.configs import Settings
from src.custom_logger import setup_logger
from src.models import SearchOutput

MAX_SEARCH_RESULTS = 3

logger = setup_logger(__name__)

class SearchQueryInput(BaseModel):
    """検索クエリ"""
    query: str = Field(description="検索クエリ")

@tool(args_schema=SearchQueryInput)
def search_xyz_qa(query: str) -> list[SearchOutput]:
    logger.info(f"Searching XYZ QA by query: {query}")

    qdrant_client = QdrantClient("http://localhost:6333")

    settings = Settings()
    openai_client = OpenAI(api_key=settings.openai_api_key)

    logger.info("Generating embedding vector from input query")
    query_vector = (
        openai_client.embeddings.create(input=query, model="text-embedding-3-small")
        .data[0]
        .embedding
    )

    search_results = qdrant_client.query_points(
        collection_name="documents",
        query=query_vector,
        limit=MAX_SEARCH_RESULTS
    ).points

    logger.info(f"Search results: {len(search_results)} hits")
    outputs = []

    for point in search_results:
        outputs.append(SearchOutput.from_point(point))

    logger.info("Finished searching XYZ QA by query")

    return outputs