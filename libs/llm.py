from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
import os

llm = ChatOpenAI(model="o3-mini-2025-01-31", api_key=os.getenv("OPENAI_API_KEY"))
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", api_key=os.getenv("OPENAI_API_KEY"))
