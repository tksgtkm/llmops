from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from src.llms.models.llm_response import LLMResponse

load_dotenv()

COST = {
    "gpt-5.5": {
        "input": 5,
        "output": 30
    },
    
}