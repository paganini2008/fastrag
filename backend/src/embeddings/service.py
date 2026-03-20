"""
Embedding service — wraps LlamaIndex OpenAIEmbedding.
"""
import logging
from typing import List
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using LlamaIndex OpenAIEmbedding."""

    def __init__(self, model: str = None):
        self.model = model or settings.DEFAULT_EMBEDDING_MODEL
        self._embedder = None

    @property
    def embedder(self):
        if self._embedder is None:
            from llama_index.embeddings.openai import OpenAIEmbedding
            self._embedder = OpenAIEmbedding(
                model=self.model,
                api_key=settings.OPENAI_API_KEY,
            )
        return self._embedder

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        text = text.replace("\n", " ").strip()
        return self.embedder.get_text_embedding(text)

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Embed a list of texts in batches."""
        texts = [t.replace("\n", " ").strip() for t in texts]
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            all_embeddings.extend(self.embedder.get_text_embedding_batch(batch, show_progress=False))
            logger.debug(f"Embedded batch {i // batch_size + 1}, total={len(all_embeddings)}")
        return all_embeddings
