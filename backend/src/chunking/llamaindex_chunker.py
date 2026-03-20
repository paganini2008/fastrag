"""
LlamaIndex-backed chunkers.

  SentenceSplitterChunker  — fast, deterministic, sentence-aware (default)
  SemanticSplitterChunker  — embedding-based semantic boundary detection
"""
import logging
from typing import List
from .service import BaseChunker, Chunk

logger = logging.getLogger(__name__)


class SentenceSplitterChunker(BaseChunker):
    """
    Wraps llama_index.core.node_parser.SentenceSplitter.
    Splits at sentence boundaries; chunk_size and chunk_overlap are in tokens.
    """

    def split_text(self, text: str, page: int = 1) -> List[Chunk]:
        from llama_index.core.node_parser import SentenceSplitter
        from llama_index.core.schema import Document as LlamaDocument

        splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        nodes = splitter.get_nodes_from_documents([LlamaDocument(text=text)])
        return [
            Chunk(
                text=node.text,
                chunk_index=i,
                page=page,
                token_count=len(node.text.split()),
            )
            for i, node in enumerate(nodes)
        ]


class SemanticSplitterChunker(BaseChunker):
    """
    Wraps llama_index.core.node_parser.SemanticSplitterNodeParser.
    Groups sentences into semantically coherent chunks using embedding similarity.
    Requires OPENAI_API_KEY.
    """

    def split_text(self, text: str, page: int = 1) -> List[Chunk]:
        from django.conf import settings
        from llama_index.core.node_parser import SemanticSplitterNodeParser
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.core.schema import Document as LlamaDocument

        embed_model = OpenAIEmbedding(api_key=settings.OPENAI_API_KEY)
        splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=embed_model,
        )
        nodes = splitter.get_nodes_from_documents([LlamaDocument(text=text)])
        return [
            Chunk(
                text=node.text,
                chunk_index=i,
                page=page,
                token_count=len(node.text.split()),
            )
            for i, node in enumerate(nodes)
        ]
