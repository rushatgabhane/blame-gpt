from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from libs.rate_limiter import rate_limited_openai
import os

# Initialize base models
_llmReasoningCheap = ChatOpenAI(model="o3-mini-2025-01-31", api_key=os.getenv("OPENAI_API_KEY"))
_llmReasoning = ChatOpenAI(model="o3-2025-04-16", api_key=os.getenv("OPENAI_API_KEY"))
_llmCheap = ChatOpenAI(model="gpt-4.1-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.2)
_embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", api_key=os.getenv("OPENAI_API_KEY"))


# Rate-limited models
class RateLimitedChatOpenAI:
    def __init__(self, base_model):
        self._model = base_model

    @rate_limited_openai
    def invoke(self, *args, **kwargs):
        return self._model.invoke(*args, **kwargs)

    @rate_limited_openai
    def stream(self, *args, **kwargs):
        return self._model.stream(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._model, name)


class RateLimitedOpenAIEmbeddings:
    def __init__(self, base_model):
        self._model = base_model

    @rate_limited_openai
    def embed_query(self, *args, **kwargs):
        return self._model.embed_query(*args, **kwargs)

    @rate_limited_openai
    def embed_documents(self, *args, **kwargs):
        return self._model.embed_documents(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._model, name)


# Export rate-limited models
llmReasoningCheap = RateLimitedChatOpenAI(_llmReasoningCheap)
llmReasoning = RateLimitedChatOpenAI(_llmReasoning)
llmCheap = RateLimitedChatOpenAI(_llmCheap)
embedding_model = RateLimitedOpenAIEmbeddings(_embedding_model)
