import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

api_key = SecretStr(os.getenv("OPENAI_API_KEY") or "")
if not api_key.get_secret_value():
    raise Exception("OpenAI API key not found. Make sure to set the `OPENAI_API_KEY` environment variable")

llmReasoningCheap = ChatOpenAI(model="o3-mini-2025-01-31", api_key=api_key)
llmReasoning = ChatOpenAI(model="o3-2025-04-16", api_key=api_key)
llmCheap = ChatOpenAI(model="gpt-4.1-mini", api_key=api_key, temperature=0.2)
llmNano = ChatOpenAI(model="gpt-4.1-nano-2025-04-14", api_key=api_key, temperature=0.2)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", api_key=api_key)
