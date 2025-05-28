from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
import os

llm = ChatOpenAI(model="gpt-4.1-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.2)
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large", api_key=os.getenv("OPENAI_API_KEY")
)
