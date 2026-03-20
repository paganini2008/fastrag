"""
Prompt Builder — constructs enhanced prompts from retrieved chunks.
"""
from typing import List
from .service import RetrievedChunk

SYSTEM_PROMPT = """You are a helpful AI assistant. Answer the user's question based ONLY on the provided context.
If the context does not contain enough information to answer, say so clearly.
Always cite your sources by referencing the context number [1], [2], etc."""


class PromptBuilder:

    def build(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        system_prompt: str = None,
    ) -> dict:
        system = system_prompt or SYSTEM_PROMPT

        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            source_label = chunk.source_name
            if chunk.page:
                source_label += f" (page {chunk.page})"
            elif chunk.url:
                source_label += f" ({chunk.url})"
            context_parts.append(f"[{i}] Source: {source_label}\n{chunk.text}")

        context_block = "\n\n---\n\n".join(context_parts)

        full_prompt = (
            f"{system}\n\n"
            f"Context:\n{context_block}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )

        token_estimate = len(full_prompt) // 4  # rough estimate

        return {
            "system": system,
            "context_block": context_block,
            "user": query,
            "full_prompt": full_prompt,
            "token_estimate": token_estimate,
        }


prompt_builder = PromptBuilder()
