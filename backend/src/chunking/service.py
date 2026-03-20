"""
Text chunking service — all strategies backed by LlamaIndex.

  sentence  (default) — SentenceSplitter, sentence-aware, chunk_size in tokens
  semantic            — SemanticSplitterNodeParser, embedding-based boundaries
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    chunk_index: int
    page: int = 1
    section: str = ""
    token_count: int = 0
    metadata: dict = field(default_factory=dict)


class BaseChunker(ABC):
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def split_text(self, text: str, page: int = 1) -> List[Chunk]: ...

    def split_pages(self, pages: List[dict]) -> List[Chunk]:
        all_chunks: List[Chunk] = []
        global_index = 0
        for page_data in pages:
            for chunk in self.split_text(page_data["text"], page=page_data["page"]):
                chunk.chunk_index = global_index
                all_chunks.append(chunk)
                global_index += 1
        return all_chunks


_STRATEGIES: dict[str, str] = {
    "sentence": "chunking.llamaindex_chunker.SentenceSplitterChunker",
    "semantic": "chunking.llamaindex_chunker.SemanticSplitterChunker",
}


def get_chunker(
    strategy: str = "sentence",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    **kwargs,
) -> BaseChunker:
    """
    Instantiate a chunker by strategy name.

    Strategies: "sentence" (default) | "semantic"
    """
    import importlib
    path = _STRATEGIES.get(strategy)
    if path is None:
        raise ValueError(
            f"Unknown chunking strategy '{strategy}'. "
            f"Available: {list(_STRATEGIES)}"
        )
    module_path, class_name = path.rsplit(".", 1)
    cls = getattr(importlib.import_module(module_path), class_name)
    return cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs)
