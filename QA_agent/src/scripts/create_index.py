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