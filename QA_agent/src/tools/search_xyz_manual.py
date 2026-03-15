from elasticsearch import Elasticsearch
from langchain.tools import tool
from pydantic import BaseModel, Field

from src.custom_logger import setup_logger
from src.models import SearchOutput

MAX_SEARCH_RESULTS = 3

logger = setup_logger(__file__)

class SearchKeywordInput(BaseModel):
    keywords: str = Field(description="全文検索用のキーワード")

@tool(args_schema=SearchKeywordInput)
def search_xyz_manual(keywords: str) -> list[SearchOutput]:
    """
    XYZシステムのドキュメントを調査する関数。
    エラーコードや固有名詞が質問に含まれる場合は、この関数を使ってキーワード検索を行う。
    """
    logger.info(f"Searching XYZ manual by keyword: {keywords}")

    es = Elasticsearch("http://localhost:9200")

    index_name = "documents"

    keyword_query = {"query": {"match": {"content": keywords}}}

    response = es.search(index=index_name, body=keyword_query)

    logger.info(f"Search results: {len(response['hits']['hits'])} hits")

    outputs = []

    for hit in response["hits"]["hits"][:MAX_SEARCH_RESULTS]:
        outputs.append(SearchOutput.from_hit(hit))
    
    logger.info("Finished searching XYZ manual by keyword")

    return outputs