import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

llmReasoningCheap = ChatOpenAI(model="o3-mini-2025-01-31", api_key=os.getenv("OPENAI_API_KEY"))
llmReasoning = ChatOpenAI(model="o3-2025-04-16", api_key=os.getenv("OPENAI_API_KEY"))
llmCheap = ChatOpenAI(model="gpt-4.1-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.2)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", api_key=os.getenv("OPENAI_API_KEY"))
