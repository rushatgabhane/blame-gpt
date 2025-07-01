from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from libs.rate_limiter import rate_limited_openai
import os


# Lazy initialization for OpenAI models
class LazyOpenAIModel:
    def __init__(self, model_class, *args, **kwargs):
        self._model_class = model_class
        self._args = args
        self._kwargs = kwargs
        self._model = None

    def _get_model(self):
        if self._model is None:
            self._model = self._model_class(*self._args, **self._kwargs)
        return self._model

    def __getattr__(self, name):
        return getattr(self._get_model(), name)


# Rate-limited models with lazy initialization
class RateLimitedChatOpenAI:
    def __init__(self, model_class, *args, **kwargs):
        self._lazy_model = LazyOpenAIModel(model_class, *args, **kwargs)

    @rate_limited_openai
    def invoke(self, *args, **kwargs):
        return self._lazy_model.invoke(*args, **kwargs)

    @rate_limited_openai
    def stream(self, *args, **kwargs):
        return self._lazy_model.stream(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._lazy_model, name)


class RateLimitedOpenAIEmbeddings:
    def __init__(self, model_class, *args, **kwargs):
        self._lazy_model = LazyOpenAIModel(model_class, *args, **kwargs)

    @rate_limited_openai
    def embed_query(self, *args, **kwargs):
        return self._lazy_model.embed_query(*args, **kwargs)

    @rate_limited_openai
    def embed_documents(self, *args, **kwargs):
        return self._lazy_model.embed_documents(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._lazy_model, name)


# Export rate-limited models with lazy initialization
llmReasoningCheap = RateLimitedChatOpenAI(ChatOpenAI, model="o3-mini-2025-01-31", api_key=os.getenv("OPENAI_API_KEY"))
llmReasoning = RateLimitedChatOpenAI(ChatOpenAI, model="o3-2025-04-16", api_key=os.getenv("OPENAI_API_KEY"))
llmCheap = RateLimitedChatOpenAI(ChatOpenAI, model="gpt-4.1-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.2)
embedding_model = RateLimitedOpenAIEmbeddings(
    OpenAIEmbeddings, model="text-embedding-3-large", api_key=os.getenv("OPENAI_API_KEY")
)
