import os
from glob import glob

from elasticsearch import Elasticsearch, helpers
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

class Settings(BaseSettings):
    openai_api_key: str
    openai_api_base: str
    openai_model: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

def load_pdf_docs(data_dir_path: str) -> list[Document]:
    pdf_path = glob(os.path.join(data_dir_path, "**", "*.pdf"), recursive=True)
    docs = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False
    )
    for path in pdf_path:
        loader = PyPDFLoader(path)
        pages = loader.load_and_split(text_splitter)
        docs.extend(pages)

    return docs

def load_csv_docs(data_dir_path: str) -> list[Document]:
    csv_path = glob(os.path.join(data_dir_path, "**", "*.csv"), recursive=True)
    docs = []

    for path in csv_path:
        loader = CSVLoader(file_path=path)
        docs.extend(loader.load())
    return docs

def create_keyword_search_index(es: Elasticsearch, index_name: str) -> None:
    mapping = {
        "mappings": {
            "properties": {
                "content": {
                    "type": "text",
                    "analyzer": "kuromoji_analyzer",
                }
            },
        },
        "settings": {
            "analysis": {
                "analyzer": {
                    "kuromoji_analyzer": {
                        "type": "custom",
                        "char_filter": ["icu_normalizer"],
                        "tokenizer": "kuromoji_tokenizer",
                        "filter": [
                            "kuromoji_baseform",
                            "kuromoji_part_of_speech",
                            "ja_stop",
                            "kuromoji_number",
                            "kuromoji_stemmer",
                        ],
                    }
                }
            }
        },
    }

    if not es.indices.exists(index=index_name):
        result = es.indices.create(index=index_name, body=mapping)
        if result:
            print(f"Index {index_name} created successfully")
        else:
            print(f"Failed to create index {index_name}")

def create_vector_search_index(qdrant_client: QdrantClient, index_name: str) -> None:
    result = qdrant_client.create_collection(
        collection_name=index_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )

    if result:
        print(f"Collection {index_name} created successfully")
    else:
        print(f"Failed to create collection {index_name}")

def add_documents_to_es(es: Elasticsearch, index_name: str, docs: list[Document]) ->None:
    insert_docs = []

    for doc in docs:
        content = doc.page_content

        insert_doc = {
            "_index": index_name,
            "_source": {
                "file_name": os.path.basename(doc.metadata["source"]),
                "content": content
            },
        }
        insert_docs.append(insert_doc)

    helpers.bulk(es, insert_docs)

def add_documents_to_qdrant(
        qdrant_client: QdrantClient, 
        index_name: str, 
        docs: list[Document], 
        settings: Settings
    ) -> None:
    points = []
    client = OpenAI(api_key=settings.openai_api_key)

    for i, doc in enumerate(docs):
        content = doc.page_content
        content = content.replace(" ", "")
        embedding = client.embeddings.create(
            model="text-embedding-3-small",
            input=content
        )
        points.append(
            PointStruct(
                id=i,
                vector=embedding.data[0].embedding,
                payload={
                    "file_name": os.path.basename(doc.metadata["source"]),
                    "content": content
                },
            )
        )
    
    operation_info = qdrant_client.upsert(
        collection_name=index_name,
        points=points,
        wait=True
    )

    print(operation_info)

if __name__ == "__main__":
    es = Elasticsearch("http://localhost:9200")
    qdrant_client = QdrantClient("http://localhost:6333")

    settings = Settings()

    index_name = "documents"
    print(f"Creating index for keyword search {index_name}")
    create_keyword_search_index(es, index_name)
    print("--------------------------------")

    print(f"Creating index for vector search {index_name}")
    create_vector_search_index(qdrant_client, index_name)
    print("--------------------------------")
    print("Loading documents from manual data")
    manual_docs = load_pdf_docs(data_dir_path="data")
    print(f"Loaded {len(manual_docs)} documents")

    print("--------------------------------")
    print("Loading documents from qa data")
    qa_docs = load_csv_docs(data_dir_path="data")
    print(f"Loaded {len(qa_docs)} documents")

    print("Adding documents to keyword search index")
    add_documents_to_es(es, index_name, manual_docs)
    print("--------------------------------")

    print("Adding documents to vector search index")
    add_documents_to_qdrant(qdrant_client, index_name, qa_docs, settings)
    print("--------------------------------")
    print("Done")