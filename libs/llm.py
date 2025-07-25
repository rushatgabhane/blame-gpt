import os
from dataclasses import dataclass

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr


class ModelNames:
    GPT_4_1 = "gpt-4.1-2025-04-14"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano-2025-04-14"
    O3_MINI = "o3-mini-2025-01-31"
    O3 = "o3-2025-04-16"


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
    ModelNames.GPT_4_1: LLMPricing(
        name=ModelNames.GPT_4_1,
        input_price_per_million=2.0,
        output_price_per_million=8.0,
        reasoning_price_per_million=8.0,
    ),
    ModelNames.GPT_4_1_MINI: LLMPricing(
        name=ModelNames.GPT_4_1_MINI,
        input_price_per_million=0.4,
        output_price_per_million=1.6,
        reasoning_price_per_million=1.6,
    ),
    ModelNames.GPT_4_1_NANO: LLMPricing(
        name=ModelNames.GPT_4_1_NANO,
        input_price_per_million=0.1,
        output_price_per_million=0.4,
        reasoning_price_per_million=0.4,
    ),
    ModelNames.O3_MINI: LLMPricing(
        name=ModelNames.O3_MINI,
        input_price_per_million=1.1,
        output_price_per_million=4.4,
        reasoning_price_per_million=4.4,
    ),
    ModelNames.O3: LLMPricing(
        name=ModelNames.O3,
        input_price_per_million=2.0,
        output_price_per_million=8.0,
        reasoning_price_per_million=8.0,
    ),
}

api_key = SecretStr(os.getenv("OPENAI_API_KEY") or "")
huggingface_api_key = SecretStr(os.getenv("HUGGINGFACE_API_KEY") or "")

llmReasoningCheap = ChatOpenAI(model=ModelNames.O3_MINI, api_key=api_key)
llmReasoning = ChatOpenAI(model=ModelNames.O3, api_key=api_key)
llm = ChatOpenAI(model=ModelNames.GPT_4_1, api_key=api_key, temperature=0.2)
llmCheap = ChatOpenAI(model=ModelNames.GPT_4_1_MINI, api_key=api_key, temperature=0.2)
llmNano = ChatOpenAI(model=ModelNames.GPT_4_1_NANO, api_key=api_key, temperature=0.2)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", api_key=api_key)

llmCodingModelCheapKimi = ChatOpenAI(
    model="moonshotai/kimi-k2-instruct",
    base_url="https://router.huggingface.co/novita/v3/openai",
    api_key=huggingface_api_key,
    temperature=0,
)

llmCodingModelCheapQwen = ChatOpenAI(
    model="Qwen/Qwen3-Coder-480B-A35B-Instruct:novita",
    base_url="https://router.huggingface.co/v1",
    api_key=huggingface_api_key,
    temperature=0,
)

if bool(os.getenv("USE_CHEAP_LLM_ONLY")):
    # Reassign the models to use the cheaper and non reasoning models
    llmReasoning = ChatOpenAI(model=ModelNames.GPT_4_1_MINI, api_key=api_key)
    llmReasoningCheap = ChatOpenAI(model=ModelNames.GPT_4_1_MINI, api_key=api_key)
