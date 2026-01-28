from pydantic import BaseModel


class LLMModelConfig(BaseModel):
    """Configuration for the LLM model connection.
    Contains:
    - api_token: API token for authentication.
    - model_name: Name of the LLM model to use.
    - temperature: (Optional) Temperature setting for the model.
    - max_tokens: (Optional) Maximum number of tokens for the model response.
    """

    api_token: str
    model_name: str
    temperature: float | None = None
    max_tokens: int | None = None
