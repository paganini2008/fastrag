"""
Application DI Container.

Uses dependency-injector to manage all service singletons.
Singletons are constructed lazily on first access, so external services
(MinIO, Qdrant, Redis) are not contacted at import time — only when needed.

Usage
-----
From anywhere in Django / Celery:

    from config.container import container

    minio  = container.minio_client()
    vs     = container.vector_store()
    parser = container.document_parser()

In views/tasks with @inject:

    from dependency_injector.wiring import inject, Provide
    from config.container import container

    @inject
    def my_view(request, retrieval_svc=Provide[container.retrieval_service]):
        result = retrieval_svc.search(...)

Overriding in tests:

    with container.retrieval_service.override(mock_service):
        response = client.post(...)
"""
from dependency_injector import containers, providers


class AppContainer(containers.DeclarativeContainer):

    # ── Object storage ────────────────────────────────────────────────────────
    minio_client = providers.Singleton(
        "common.storage.MinIOClient",
    )

    # ── Vector database ───────────────────────────────────────────────────────
    vector_store = providers.Singleton(
        "vector_store.service.VectorStoreService",
    )

    # ── Embedding ─────────────────────────────────────────────────────────────
    embedding_service = providers.Singleton(
        "embeddings.service.EmbeddingService",
    )

    # ── Document processing ───────────────────────────────────────────────────
    document_parser = providers.Singleton(
        "parsers.llamaindex_parser.LlamaIndexParser",
    )

    # Chunker factory — returns a callable that accepts (chunk_size, chunk_overlap)
    # For a per-KB chunker (different sizes per KB), call get_chunker() directly
    # from chunking.service; the container manages only the default instance.
    default_chunker = providers.Singleton(
        "chunking.llamaindex_chunker.SentenceSplitterChunker",
    )

    # ── Retrieval & RAG ───────────────────────────────────────────────────────
    retrieval_service = providers.Singleton(
        "retrieval.service.RetrievalService",
        vector_store=vector_store,
    )

    answer_service = providers.Singleton(
        "retrieval.answer_service.AnswerService",
        retrieval_svc=retrieval_service,
    )


# Module-level singleton — wire once, use everywhere
container = AppContainer()
