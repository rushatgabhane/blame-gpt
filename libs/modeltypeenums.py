from enum import Enum


class ModelType(Enum):
    LOCAL = "local"
    OPENAI = "openai"


class ModelThinkingType(Enum):
    FOUNDATIONAL = "foundational"
    REASONING = "reasoningCheap"
    EMBEDDING = "embedding"


class ModelCostType(Enum):
    DEFAULT = "default"
    CHEAP = "cheap"
    STANDARD = "standard"
