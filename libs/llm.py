from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(
    model="gpt-4o-mini", openai_api_key=os.getenv("OPENAI_API_KEY")
)
