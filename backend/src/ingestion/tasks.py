"""
Background ingestion tasks — run in a thread pool, no external broker needed.

Document.status is the single source of truth for progress:
  pending → parsing → parsed → chunking → chunked → embedding → indexed
                                                                → failed
"""
import atexit
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from django.utils import timezone
from config.container import container

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ingestion")
atexit.register(lambda: _executor.shutdown(wait=False))


def run_async(fn, *args, **kwargs):
    """Submit a callable to the background thread pool."""
    future = _executor.submit(fn, *args, **kwargs)
    future.add_done_callback(_log_exception)
    return future


def _log_exception(future):
    exc = future.exception()
    if exc:
        logger.exception("Background task failed", exc_info=exc)


# ─── Pipeline entry points ────────────────────────────────────────────────────

def ingest_document(document_id: str):
    """Full ingestion pipeline: parse → chunk → embed → index."""
    from documents.models import Document

    try:
        doc = Document.objects.select_related("knowledge_base").get(id=document_id)
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return

    _parse_document(doc)
    if doc.status == Document.Status.FAILED:
        return

    _chunk_document(doc)
    if doc.status == Document.Status.FAILED:
        return

    _embed_document(doc)


def ingest_url(document_id: str, url_source_id: str):
    """Fetch URL content, store in MinIO, then run ingest_document."""
    from documents.models import Document, URLSource

    minio = container.minio_client()

    try:
        doc = Document.objects.select_related("knowledge_base").get(id=document_id)
        url_source = URLSource.objects.get(id=url_source_id)
    except (Document.DoesNotExist, URLSource.DoesNotExist) as e:
        logger.error(f"ingest_url: {e}")
        return

    try:
        html_content = _fetch_url(url_source.url, url_source.render_mode)
        object_key = f"raw/{doc.tenant_id}/{doc.id}/page.html"
        minio.put_bytes(object_key, html_content.encode("utf-8"), "text/html")

        doc.file_path = object_key
        doc.mime_type = "text/html"
        doc.save(update_fields=["file_path", "mime_type"])

        url_source.html_path = object_key
        url_source.last_crawled_at = timezone.now()
        url_source.status = "fetched"
        url_source.save()

        ingest_document(document_id)

    except Exception as e:
        logger.exception(f"URL fetch failed: {url_source.url}")
        doc.status = Document.Status.FAILED
        doc.error_message = str(e)
        doc.save(update_fields=["status", "error_message"])


def _build_chunk_payload(doc, chunk, embedding_model: str) -> dict:
    return {
        "tenant_id": str(doc.tenant_id),
        "knowledge_base_id": str(doc.knowledge_base_id),
        "document_id": str(doc.id),
        "chunk_id": str(chunk.id),
        "chunk_index": chunk.chunk_index,
        "text": chunk.text,
        "source_type": doc.source_type,
        "source_name": doc.name,
        "page": chunk.page,
        "url": doc.source_url or None,
        "mime_type": doc.mime_type,
        "embedding_model": embedding_model,
        "created_at": chunk.created_at.isoformat(),
    }


def rebuild_knowledge_base(kb_id: str, new_embedding_model: str):
    """
    Re-embed all indexed documents in a KB using a new embedding model.
    Reads chunk text from DB (no re-parsing), writes to a per-KB Qdrant collection.
    """
    from django.conf import settings
    from knowledge_bases.models import KnowledgeBase
    from documents.models import Document, DocumentChunk
    from embeddings.constants import MODEL_DIMENSIONS
    from embeddings.service import EmbeddingService
    from qdrant_client.models import FilterSelector, Filter, FieldCondition, MatchValue
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from llama_index.core.schema import TextNode

    vs = container.vector_store()
    client = vs.client

    vector_size = MODEL_DIMENSIONS[new_embedding_model]
    new_collection = f"{settings.QDRANT_COLLECTION}_kb_{kb_id.replace('-', '')}"

    try:
        # Step 1: delete existing per-KB collection if any
        if client.collection_exists(new_collection):
            client.delete_collection(new_collection)

        # Step 2: delete old vectors from shared collection (ignore if not found)
        try:
            client.delete(
                collection_name=vs.collection,
                points_selector=FilterSelector(
                    filter=Filter(must=[FieldCondition(
                        key="knowledge_base_id", match=MatchValue(value=str(kb_id))
                    )])
                ),
            )
        except Exception:
            pass

        # Step 3: create new collection (delegates creation + indexes to VectorStoreService)
        vs.ensure_collection(collection_name=new_collection, vector_size=vector_size)

        qdrant_store = QdrantVectorStore(client=client, collection_name=new_collection)
        embedder = EmbeddingService(model=new_embedding_model)

        # Fetch all chunks in one query, grouped by document — avoids N+1
        docs = list(Document.objects.filter(
            knowledge_base_id=kb_id, status=Document.Status.INDEXED
        ))
        total = len(docs)
        doc_map = {doc.id: doc for doc in docs}

        all_chunks = (
            DocumentChunk.objects
            .filter(knowledge_base_id=kb_id)
            .order_by("document_id", "chunk_index")
        )
        chunks_by_doc: dict = {}
        for chunk in all_chunks:
            chunks_by_doc.setdefault(chunk.document_id, []).append(chunk)

        for doc_idx, doc in enumerate(docs):
            chunks = chunks_by_doc.get(doc.id, [])

            for i in range(0, len(chunks), 100):
                batch = chunks[i:i + 100]
                embeddings = embedder.embed_batch([c.text for c in batch])

                nodes = []
                for chunk, embedding in zip(batch, embeddings):
                    payload = _build_chunk_payload(doc, chunk, new_embedding_model)
                    node = TextNode(id_=str(chunk.id), text=chunk.text, metadata=payload)
                    node.embedding = embedding
                    nodes.append(node)
                    chunk.embedding_model = new_embedding_model

                qdrant_store.add(nodes)
                DocumentChunk.objects.bulk_update(batch, ["embedding_model"])

            # Update progress every 5 docs to reduce DB writes
            if total > 0 and (doc_idx + 1) % 5 == 0:
                progress = int((doc_idx + 1) / total * 95)
                KnowledgeBase.objects.filter(id=kb_id).update(rebuild_progress=progress)

        KnowledgeBase.objects.filter(id=kb_id).update(
            embedding_model=new_embedding_model,
            vector_size=vector_size,
            collection_name=new_collection,
            rebuild_status="done",
            rebuild_progress=100,
        )
        logger.info(f"Rebuild complete for KB {kb_id} → {new_embedding_model}")

    except Exception:
        logger.exception(f"Rebuild failed for KB {kb_id}")
        KnowledgeBase.objects.filter(id=kb_id).update(
            rebuild_status="failed", rebuild_progress=0
        )


def embed_faq_item(faq_item_id: str):
    """Embed a single FAQ item."""
    from faq.models import FAQItem
    from embeddings.service import EmbeddingService

    vs = container.vector_store()

    try:
        item = FAQItem.objects.select_related("knowledge_base").get(id=faq_item_id)
    except FAQItem.DoesNotExist:
        return

    kb = item.knowledge_base
    collection = kb.collection_name or vs.collection
    vs.ensure_collection(collection_name=collection, vector_size=kb.vector_size)

    embedder = EmbeddingService(model=kb.embedding_model)

    text = f"Q: {item.question}\nA: {item.answer}"
    embedding = embedder.embed_text(text)

    point = {
        "id": str(item.id),
        "vector": embedding,
        "payload": {
            "tenant_id": str(item.tenant_id),
            "knowledge_base_id": str(item.knowledge_base_id),
            "document_id": str(item.id),
            "chunk_id": str(item.id),
            "chunk_index": 0,
            "text": text,
            "source_type": "faq",
            "source_name": "FAQ",
            "page": None,
            "url": None,
            "mime_type": "text/plain",
            "embedding_model": kb.embedding_model,
            "created_at": item.created_at.isoformat(),
        },
    }
    vs.upsert_chunks([point], collection_name=collection)

    item.vector_id = str(item.id)
    item.is_embedded = True
    item.save(update_fields=["vector_id", "is_embedded"])


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _parse_document(doc):
    from documents.models import Document

    minio = container.minio_client()
    parser = container.document_parser()

    doc.status = Document.Status.PARSING
    doc.save(update_fields=["status"])

    try:
        file_data = minio.get_object(doc.file_path)
        result = parser.parse_bytes(file_data, doc.mime_type, doc.name)

        doc.page_count = result.page_count
        doc.word_count = result.word_count
        doc.status = Document.Status.PARSED
        doc.meta["parsed_pages"] = [{"page": p.page, "text": p.text} for p in result.pages]
        doc.save(update_fields=["page_count", "word_count", "status", "meta"])

    except Exception as e:
        logger.exception(f"Parse failed for doc {doc.id}")
        doc.status = Document.Status.FAILED
        doc.error_message = str(e)
        doc.save(update_fields=["status", "error_message"])


def _chunk_document(doc):
    from documents.models import Document, DocumentChunk
    from chunking.service import get_chunker

    doc.status = Document.Status.CHUNKING
    doc.save(update_fields=["status"])

    try:
        kb = doc.knowledge_base
        strategy = kb.settings.get("chunking_strategy", "sentence") if kb.settings else "sentence"
        chunker = get_chunker(
            strategy=strategy,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
        )

        chunks = chunker.split_pages(doc.meta.get("parsed_pages", []))

        DocumentChunk.objects.filter(document=doc).delete()
        DocumentChunk.objects.bulk_create([
            DocumentChunk(
                tenant_id=doc.tenant_id,
                knowledge_base=doc.knowledge_base,
                document=doc,
                chunk_index=c.chunk_index,
                text=c.text,
                text_length=len(c.text),
                token_count=c.token_count,
                page=c.page,
            )
            for c in chunks
        ], batch_size=500)

        doc.chunk_count = len(chunks)
        doc.status = Document.Status.CHUNKED
        doc.save(update_fields=["chunk_count", "status"])

    except Exception as e:
        logger.exception(f"Chunking failed for doc {doc.id}")
        doc.status = Document.Status.FAILED
        doc.error_message = str(e)
        doc.save(update_fields=["status", "error_message"])


def _embed_document(doc):
    from documents.models import Document, DocumentChunk
    from embeddings.service import EmbeddingService
    from django.db.models import Count

    vs = container.vector_store()

    doc.status = Document.Status.EMBEDDING
    doc.save(update_fields=["status"])

    try:
        chunks = list(DocumentChunk.objects.filter(document=doc, is_embedded=False))
        kb = doc.knowledge_base
        embedder = EmbeddingService(model=kb.embedding_model)
        collection = kb.collection_name or vs.collection
        vs.ensure_collection(collection_name=collection, vector_size=kb.vector_size)

        for i in range(0, len(chunks), 100):
            batch = chunks[i:i + 100]
            embeddings = embedder.embed_batch([c.text for c in batch])

            points = []
            for chunk, embedding in zip(batch, embeddings):
                points.append({
                    "id": str(chunk.id),
                    "vector": embedding,
                    "payload": _build_chunk_payload(doc, chunk, kb.embedding_model),
                })
                chunk.vector_id = str(chunk.id)
                chunk.embedding_model = kb.embedding_model
                chunk.is_embedded = True

            vs.upsert_chunks(points, collection_name=collection)
            DocumentChunk.objects.bulk_update(batch, ["vector_id", "embedding_model", "is_embedded"])

        # Update KB stats in one query
        from knowledge_bases.models import KnowledgeBase
        chunk_count = DocumentChunk.objects.filter(knowledge_base=kb, is_embedded=True).aggregate(
            count=Count("id")
        )["count"] or 0
        doc_count = Document.objects.filter(
            knowledge_base=kb, status=Document.Status.INDEXED
        ).count() + 1
        KnowledgeBase.objects.filter(id=kb.id).update(chunk_count=chunk_count, doc_count=doc_count)

        doc.status = Document.Status.INDEXED
        doc.save(update_fields=["status"])

    except Exception as e:
        logger.exception(f"Embedding failed for doc {doc.id}")
        doc.status = Document.Status.FAILED
        doc.error_message = str(e)
        doc.save(update_fields=["status", "error_message"])


def _fetch_url(url: str, render_mode: str) -> str:
    if render_mode == "static":
        import requests
        resp = requests.get(url, timeout=30, headers={"User-Agent": "RAG-Bot/1.0"})
        resp.raise_for_status()
        return resp.text
    elif render_mode == "playwright":
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")
            html = page.content()
            browser.close()
            return html
    elif render_mode == "selenium":
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # macOS: Chrome is not on PATH — point to the app binary explicitly
        import platform, shutil
        if platform.system() == "Darwin" and not shutil.which("google-chrome"):
            options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return driver.page_source
        finally:
            driver.quit()
    else:
        raise ValueError(f"Unknown render_mode: {render_mode}")
