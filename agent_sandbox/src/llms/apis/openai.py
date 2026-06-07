import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from src.llms.models.llm_response import LLMResponse

load_dotenv()

# https://developers.openai.com/api/docs/pricing
COST = {
    "gpt-5.5": {
        "input": 5.0 / 1_000_000,
        "output": 30.0 / 1_000_000,
    },
    "gpt-5.5-pro": {
        "input": 30.0 / 1_000_000,
        "output": 180.0 / 1_000_000
    },
    "gpt-5.4": {
        "input": 2.5 / 1_000_000,
        "output": 15.0 / 1_000_000
    },
}

def _get_message(completion):
    message = next(
        (item for item in completion.output if item.type == "message"),
        None,
    )
    if message is None:
        types = [item.type for item in completion.output]
        raise RuntimeError(f"No message item in output: {types}")
    return message

def generate_response(messages: list, model: str = "gpt-5.4", response_format: BaseModel | None = None) -> LLMResponse:
    assert model in COST, f"Invalid model name: {model}"
    content_idx = 1 if model.endswith(("5.3", "5.4")) else 0
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if response_format is None:
        completion = client.responses.create(model=model, input=messages)
        content = _get_message(completion).content[0].text
    else:
        completion = client.responses.parse(
            model=model,
            input=messages,
            text_format=response_format
        )
        content = _get_message(completion).content[0].parsed
    input_cost = completion.usage.input_tokens * COST[model]["input"]
    output_cost = completion.usage.output_tokens * COST[model]["output"]
    return LLMResponse(
        messages=messages,
        content=content,
        model=completion.model,
        created_at=completion.created_at,
        input_tokens=completion.usage.input_tokens,
        output_tokens=completion.usage.output_tokens,
        cost=input_cost + output_cost
    )