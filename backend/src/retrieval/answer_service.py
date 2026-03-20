"""
Answer service — full LlamaIndex LLM pipeline (Anthropic + OpenAI via llm.chat()).
"""
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)


class AnswerService:

    def __init__(self, retrieval_svc=None):
        self._retrieval_svc = retrieval_svc
        self._claude_llm = None
        self._openai_llm = None

    def answer(
        self,
        query: str,
        knowledge_base_id: str,
        tenant_id: str,
        top_k: int = 5,
        llm_model: str = None,
        system_prompt: str = None,
        stream: bool = False,
        caller: str = "",
    ) -> dict:
        from .prompt_builder import prompt_builder

        llm_model = llm_model or settings.DEFAULT_LLM_MODEL
        t0 = time.time()

        result = self._retrieval_svc.search(
            query=query,
            knowledge_base_id=knowledge_base_id,
            tenant_id=tenant_id,
            top_k=top_k,
            log_caller=caller,
        )

        prompt = prompt_builder.build(query, result.chunks, system_prompt)
        answer_text, usage = self._call_llm(
            llm_model, prompt["system"], prompt["context_block"], prompt["user"]
        )

        latency_ms = int((time.time() - t0) * 1000)

        try:
            from audit.models import QueryLog
            QueryLog.objects.create(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                query=query,
                answer=answer_text,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                latency_ms=latency_ms,
                llm_model=llm_model,
                caller=caller,
            )
        except Exception:
            pass

        return {
            "query": query,
            "answer": answer_text,
            "sources": [
                {
                    "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,
                    "score": c.score,
                    "source": c.source_name + (f" (page {c.page})" if c.page else ""),
                }
                for c in result.chunks
            ],
            "usage": usage,
            "latency_ms": latency_ms,
        }

    def _call_llm(self, model: str, system: str, context_block: str, user: str):
        from llama_index.core.llms import ChatMessage, MessageRole

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system),
            ChatMessage(role=MessageRole.USER, content=f"{context_block}\n\nQuestion: {user}"),
        ]

        if model.startswith("claude"):
            return self._chat_claude(model, messages)
        return self._chat_openai(model, messages)

    def _chat_claude(self, model: str, messages):
        from llama_index.llms.anthropic import Anthropic
        if self._claude_llm is None or self._claude_llm.model != model:
            self._claude_llm = Anthropic(
                model=model, api_key=settings.ANTHROPIC_API_KEY, max_tokens=2048
            )
        response = self._claude_llm.chat(messages)
        raw = response.raw or {}
        usage_data = raw.get("usage", {})
        usage = {
            "prompt_tokens": usage_data.get("input_tokens", 0),
            "completion_tokens": usage_data.get("output_tokens", 0),
            "total_tokens": usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
        }
        return response.message.content, usage

    def _chat_openai(self, model: str, messages):
        from llama_index.llms.openai import OpenAI
        if self._openai_llm is None or self._openai_llm.model != model:
            self._openai_llm = OpenAI(
                model=model, api_key=settings.OPENAI_API_KEY, max_tokens=2048
            )
        response = self._openai_llm.chat(messages)
        raw = response.raw or {}
        usage_data = getattr(raw, "usage", None) or {}
        if hasattr(usage_data, "prompt_tokens"):
            usage = {
                "prompt_tokens": usage_data.prompt_tokens,
                "completion_tokens": usage_data.completion_tokens,
                "total_tokens": usage_data.total_tokens,
            }
        else:
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        return response.message.content, usage
