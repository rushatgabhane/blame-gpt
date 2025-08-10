import os
from dataclasses import dataclass

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr


class ModelNames:
    GPT_5 = "gpt-5-2025-08-07"
    GPT_5_MINI = "gpt-5-mini-2025-08-07"
    GPT_5_NANO = "gpt-5-nano-2025-08-07"


@dataclass
class LLMPricing:
    """LLM pricing information per million tokens."""

    name: str
    input_price_per_million: float  # USD per 1M input tokens
    output_price_per_million: float  # USD per 1M output tokens
    reasoning_price_per_million: float  # USD per 1M reasoning tokens

    @property
    def input_price_per_token(self) -> float:
        return self.input_price_per_million / 1_000_000

    @property
    def output_price_per_token(self) -> float:
        return self.output_price_per_million / 1_000_000

    @property
    def reasoning_price_per_token(self) -> float:
        return self.reasoning_price_per_million / 1_000_000


# LLM Pricing definitions
LLM_PRICING: dict[str, LLMPricing] = {
    ModelNames.GPT_5: LLMPricing(
        name=ModelNames.GPT_5,
        input_price_per_million=1.25,
        output_price_per_million=10.0,
        reasoning_price_per_million=10.0,
    ),
    ModelNames.GPT_5_MINI: LLMPricing(
        name=ModelNames.GPT_5_MINI,
        input_price_per_million=0.25,
        output_price_per_million=2.0,
        reasoning_price_per_million=2.0,
    ),
    ModelNames.GPT_5_NANO: LLMPricing(
        name=ModelNames.GPT_5_NANO,
        input_price_per_million=0.05,
        output_price_per_million=0.4,
        reasoning_price_per_million=0.4,
    ),
}

api_key = SecretStr(os.getenv("OPENAI_API_KEY") or "")

llm = ChatOpenAI(model=ModelNames.GPT_5, api_key=api_key)
llmCheap = ChatOpenAI(model=ModelNames.GPT_5_MINI, api_key=api_key)
llmNano = ChatOpenAI(model=ModelNames.GPT_5_NANO, api_key=api_key)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", api_key=api_key)

if bool(os.getenv("USE_CHEAP_LLM_ONLY")):
    # Reassign the main model to use the cheaper model
    llm = ChatOpenAI(model=ModelNames.GPT_5_NANO, api_key=api_key)
