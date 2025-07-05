import os

from langchain_ollama.llms import OllamaLLM
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from libs.modeltypeenums import ModelCostType, ModelThinkingType


class llmFactory:
    def getLLM(
        self,
        llmType: str,
        local: bool = True,
        modelType: ModelThinkingType = ModelThinkingType.FOUNDATIONAL,
        cost: ModelCostType = ModelCostType.STANDARD,
        modelName: str = "any",
    ):
        match (llmType, local):
            case ("open-ai", False):
                print("Using OpenAI LLM Non-Local")
                return self.getOpenAILLM(modelType, cost)
            case ("local-ollama", True):
                print("Using Local LLM Ollama")
                if modelName == "any":
                    raise ValueError("Model name must be specified for local LLMs.")
                print(f"Using Local LLM: {modelName} while skipping modelType and cost")
                return self.getLocalLLM(modelName)
            case _:
                raise ValueError(f"Invalid LLM type or local setting: llmType={llmType}, local={local}")

    def getLocalLLM(self, llmType: str):
        print(f"Using Local LLM: {llmType}")
        return OllamaLLM(model=llmType)

    def getOpenAILLM(self, modelType: ModelThinkingType, cost: ModelCostType):
        match (modelType, cost):
            case (ModelThinkingType.FOUNDATIONAL, _):
                return ChatOpenAI(model="gpt-4.1-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.2)
            case (ModelThinkingType.REASONING, ModelCostType.STANDARD):
                return ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
            case (ModelThinkingType.REASONING, ModelCostType.CHEAP):
                return ChatOpenAI(model="o3-mini-2025-01-31", api_key=os.getenv("OPENAI_API_KEY"))
            case (ModelThinkingType.EMBEDDING, _):
                return OpenAIEmbeddings(model="text-embedding-3-large", api_key=os.getenv("OPENAI_API_KEY"))
            case _:
                raise ValueError(f"Unknown OpenAI LLM type: modelType={modelType}, cost={cost}")
