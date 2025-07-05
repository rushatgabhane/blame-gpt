from enum import Enum


class ModelType(Enum):
    LOCAL = "local"
    OPENAI = "openai"


class ModelThinkingType(Enum):
    FOUNDATIONAL = "foundational"
    REASONING = "reasoningCheap"
    EMBEDDING = "embedding"


class ModelCostType(Enum):
    CHEAP = "cheap"
    STANDARD = "standard"
