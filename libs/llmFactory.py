import os
from pathlib import Path

import yaml
from langchain_ollama.llms import OllamaLLM
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from libs.modeltypeenums import ModelCostType, ModelThinkingType


def load_config(config_path=None):
    # Always load config from the same folder as this script by default
    if config_path is None:
        here = Path(__file__).parent
        config_file = here / "llm_config.yml"
    else:
        config_file = Path(config_path)
    with open(config_file) as f:
        return yaml.safe_load(f)


class llmFactory:
    def __init__(self, config_path=None):
        self.config = load_config(config_path)
        self.models = self.config.get("models", {})
        self.defaults = self.config.get("defaults", {})

    def getLLM(
        self,
        modelType: ModelThinkingType = None,
        cost: ModelCostType = None,
        provider: str = None,
        llm: str = None,  # overridable logical name
    ):
        # Determine section key
        if modelType is None:
            raise ValueError("modelType is required")
        section = modelType.name.lower()  # assumes enum names like 'REASONING'

        # Get config for this section
        section_conf = self.models.get(section)
        if not section_conf:
            raise ValueError(f"Section '{section}' not found in config.")

        # Section defaults
        default_section = self.defaults.get(section, {})

        # Determine cost type
        if cost is None:
            cost = ModelCostType[default_section.get("cost", "STANDARD")]
        cost_str = cost.name if isinstance(cost, ModelCostType) else str(cost)

        # Get all models for this cost type (as list)
        model_list = section_conf.get(cost_str)
        if not model_list:
            raise ValueError(f"No models for cost type '{cost_str}' in '{section}'.")

        # Provider logic
        provider = provider or default_section.get("provider", "openai")
        filtered_model_list = [m for m in model_list if m.get("provider") == provider]
        if not filtered_model_list:
            raise ValueError(f"No models for provider '{provider}' in cost type '{cost_str}' for '{section}'.")

        # LLM logic
        llm = llm or default_section.get("llm")
        if llm:
            model_conf = next((m for m in filtered_model_list if m.get("llm") == llm), None)
            if not model_conf:
                raise ValueError(
                    f"LLM '{llm}' not found for provider '{provider}' in cost type '{cost_str}' for '{section}'."
                )
        else:
            model_conf = filtered_model_list[0]

        provider = model_conf.get("provider")
        name = model_conf.get("name")
        options = model_conf.get("options", {})

        if provider == "openai":
            if section == "embedding":
                return OpenAIEmbeddings(model=name, api_key=os.getenv("OPENAI_API_KEY"))
            else:
                return ChatOpenAI(model=name, api_key=os.getenv("OPENAI_API_KEY"), **options)
        elif provider == "ollama":
            return OllamaLLM(model=name, **options)
        else:
            raise ValueError(f"Unknown provider: {provider}")
