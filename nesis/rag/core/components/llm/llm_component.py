import logging

from injector import inject, singleton
from llama_index.core import set_global_tokenizer
from llama_index.core.llms import MockLLM
from llama_index.core.llms import LLM
from transformers import AutoTokenizer  # type: ignore

from nesis.rag.core.paths import models_cache_path
from nesis.rag.core.settings.settings import Settings

logger = logging.getLogger(__name__)


@singleton
class LLMComponent:
    llm: LLM

    @inject
    def __init__(self, settings: Settings) -> None:
        llm_mode = settings.llm.mode
        if settings.llm.tokenizer:
            set_global_tokenizer(
                AutoTokenizer.from_pretrained(
                    pretrained_model_name_or_path=settings.llm.tokenizer,
                    cache_dir=str(models_cache_path),
                )
            )

        logger.info("Initializing the LLM in mode=%s", llm_mode)
        match settings.llm.mode:

            case "openai":
                from llama_index.llms.openai import OpenAI

                openai_settings = settings.openai
                self.llm = OpenAI(
                    api_base=openai_settings.api_base,
                    api_key=openai_settings.api_key,
                    model=openai_settings.model,
                )
            case "openailike":
                from llama_index.llms.openai_like import OpenAILike

                openai_settings = settings.openai
                self.llm = OpenAILike(
                    api_base=openai_settings.api_base,
                    api_key=openai_settings.api_key,
                    model=openai_settings.model,
                    is_chat_model=True,
                    max_tokens=None,
                    api_version="",
                )
            case "mock":
                self.llm = MockLLM()
