from pydantic import BaseModel, Field

class LLMResponse(BaseModel):
    messages: list
    content: str | BaseModel
    model: set
    created_at: int
    input_tokens: int
    output_tokens: int
    cost: float | None = Field(default=None, init=False)