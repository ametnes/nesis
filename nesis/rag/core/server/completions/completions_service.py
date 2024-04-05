from injector import singleton, inject
from llama_index.core.llms import ChatMessage, MessageRole
from pydantic import BaseModel

from nesis import rag as rag

from nesis.rag.core.open_ai.extensions.context_filter import ContextFilter
from nesis.rag.core.open_ai.openai_models import (
    OpenAICompletion,
    OpenAIMessage,
)
from nesis.rag.core.open_ai.openai_models import (
    to_openai_response,
)
from nesis.rag.core.server.chat.chat_service import ChatService


class CompletionsBody(BaseModel):
    prompt: str
    system_prompt: str | None = None
    use_context: bool = False
    context_filter: ContextFilter | None = None
    include_sources: bool = True
    stream: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "How do you fry an egg?",
                    "system_prompt": "You are a rapper. Always answer with a rap.",
                    "stream": False,
                    "use_context": False,
                    "include_sources": False,
                }
            ]
        }
    }


class ChatBody(BaseModel):
    messages: list[OpenAIMessage]
    use_context: bool = False
    context_filter: ContextFilter | None = None
    include_sources: bool = True
    stream: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a rapper. Always answer with a rap.",
                        },
                        {
                            "role": "user",
                            "content": "How do you fry an egg?",
                        },
                    ],
                    "stream": False,
                    "use_context": True,
                    "include_sources": True,
                    "context_filter": {
                        "docs_ids": ["c202d5e6-7b69-4869-81cc-dd574ee8ee11"]
                    },
                }
            ]
        }
    }


@singleton
class CompletionsService:

    @inject
    def __init__(self, chart_service: ChatService) -> None:
        self._chat_service = chart_service

    def chat_completion(self, body: ChatBody) -> OpenAICompletion:
        """Given a list of messages comprising a conversation, return a response.

        Optionally include an initial `role: system` message to influence the way
        the LLM answers.

        If `use_context` is set to `true`, the model will use context coming
        from the ingested documents to create the response. The documents being used can
        be filtered using the `context_filter` and passing the document IDs to be used.
        Ingested documents IDs can be found using `/ingest/list` endpoint. If you want
        all ingested documents to be used, remove `context_filter` altogether.

        When using `'include_sources': true`, the API will return the source Chunks used
        to create the response, which come from the context provided.

        When using `'stream': true`, the API will return data chunks following [OpenAI's
        streaming model](https://platform.openai.com/docs/api-reference/chat/streaming):
        ```
        {"id":"12345","object":"completion.chunk","created":1694268190,
        "model":"rag","choices":[{"index":0,"delta":{"content":"Hello"},
        "finish_reason":null}]}
        ```
        """
        all_messages = [
            ChatMessage(content=m.content, role=MessageRole(m.role))
            for m in body.messages
        ]

        completion = self._chat_service.chat(
            messages=all_messages,
            use_context=body.use_context,
            context_filter=body.context_filter,
        )
        return to_openai_response(
            completion.response, completion.sources if body.include_sources else None
        )

    def completion(self, body: CompletionsBody) -> OpenAICompletion:
        """We recommend most users use our Chat completions API.

        Given a prompt, the model will return one predicted completion.

        Optionally include a `system_prompt` to influence the way the LLM answers.

        If `use_context`
        is set to `true`, the model will use context coming from the ingested documents
        to create the response. The documents being used can be filtered using the
        `context_filter` and passing the document IDs to be used. Ingested documents IDs
        can be found using `/ingest/list` endpoint. If you want all ingested documents to
        be used, remove `context_filter` altogether.

        When using `'include_sources': true`, the API will return the source Chunks used
        to create the response, which come from the context provided.

        When using `'stream': true`, the API will return data chunks following [OpenAI's
        streaming model](https://platform.openai.com/docs/api-reference/chat/streaming):
        ```
        {"id":"12345","object":"completion.chunk","created":1694268190,
        "model":"rag","choices":[{"index":0,"delta":{"content":"Hello"},
        "finish_reason":null}]}
        ```
        """
        messages = [OpenAIMessage(content=body.prompt, role="user")]
        # If system prompt is passed, create a fake message with the system prompt.
        if body.system_prompt:
            messages.insert(0, OpenAIMessage(content=body.system_prompt, role="system"))

        chat_body = ChatBody(
            messages=messages,
            use_context=body.use_context,
            stream=body.stream,
            include_sources=body.include_sources,
            context_filter=body.context_filter,
        )
        return self.chat_completion(chat_body)
