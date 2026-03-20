"""
Retrieval, Prompt Builder, and Answer API views.
Services are resolved via the DI container — no module-level singletons.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from config.container import container
from .prompt_builder import prompt_builder

logger = logging.getLogger(__name__)

LOG_CALLER_EXTERNAL = "external"
TOP_K_MAX = 50

_PROMPT_REQUEST_SCHEMA = {
    "application/json": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "User question"},
            "knowledge_base_id": {"type": "string", "format": "uuid"},
            "top_k": {"type": "integer", "default": 5},
        },
        "required": ["query", "knowledge_base_id"],
    }
}

_PROMPT_RESPONSE_SCHEMA = OpenApiResponse(
    description="RAG prompt ready to send to an LLM",
    response={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "context": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "score": {"type": "number"},
                        "source": {"type": "string"},
                    },
                },
            },
            "prompt": {"type": "object"},
            "token_estimate": {"type": "integer"},
        },
    },
)


@extend_schema(
    summary="Vector search — retrieve relevant chunks",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "knowledge_base_id": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
                "filters": {"type": "object"},
                "score_threshold": {"type": "number", "default": 0.0},
            },
            "required": ["query", "knowledge_base_id"],
        }
    },
    tags=["Retrieval"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def search_view(request):
    query = request.data.get("query", "").strip()
    kb_id = request.data.get("knowledge_base_id")
    top_k = int(request.data.get("top_k", 5))
    filters = request.data.get("filters", {})
    score_threshold = float(request.data.get("score_threshold", 0.0))

    if not query:
        return Response({"error": "validation_error", "message": "query is required"}, status=400)
    if not kb_id:
        return Response({"error": "validation_error", "message": "knowledge_base_id is required"}, status=400)

    retrieval_svc = container.retrieval_service()
    result = retrieval_svc.search(
        query=query,
        knowledge_base_id=kb_id,
        tenant_id=str(request.user.tenant_id),
        top_k=min(top_k, TOP_K_MAX),
        score_threshold=score_threshold,
        filters=filters,
        log_caller=str(request.user.id),
    )

    return Response({
        "query": result.query,
        "total": result.total,
        "latency_ms": result.latency_ms,
        "chunks": [
            {
                "id": c.id,
                "text": c.text,
                "score": round(c.score, 4),
                "source": {
                    "type": c.source_type,
                    "name": c.source_name,
                    "document_id": c.document_id,
                    "page": c.page,
                    "url": c.url,
                },
                "metadata": {
                    "chunk_index": c.chunk_index,
                    "knowledge_base_id": c.knowledge_base_id,
                    "embedding_model": c.embedding_model,
                },
            }
            for c in result.chunks
        ],
    })


def _build_prompt_response(query, kb_id, tenant_id, top_k, log_caller):
    retrieval_svc = container.retrieval_service()
    result = retrieval_svc.search(
        query=query,
        knowledge_base_id=kb_id,
        tenant_id=tenant_id,
        top_k=top_k,
        log_caller=log_caller,
    )
    prompt = prompt_builder.build(query, result.chunks)
    return Response({
        "query": query,
        "context": [
            {"text": c.text, "score": round(c.score, 4), "source": c.source_name}
            for c in result.chunks
        ],
        "prompt": prompt,
        "token_estimate": prompt["token_estimate"],
    })


@extend_schema(
    summary="Build RAG prompt",
    description="Retrieve relevant chunks and assemble a prompt ready to send to an LLM. Does not call the LLM.",
    request=_PROMPT_REQUEST_SCHEMA,
    responses={200: _PROMPT_RESPONSE_SCHEMA},
    tags=["RAG"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def prompt_view(request):
    query = request.data.get("query", "").strip()
    kb_id = request.data.get("knowledge_base_id")
    top_k = min(int(request.data.get("top_k", 5)), TOP_K_MAX)

    if not query or not kb_id:
        return Response({"error": "validation_error", "message": "query and knowledge_base_id are required"}, status=400)

    return _build_prompt_response(query, kb_id, str(request.user.tenant_id), top_k, str(request.user.id))


@extend_schema(
    summary="Full RAG answer (retrieval + LLM)",
    description="Retrieve relevant chunks, build a prompt, call the LLM, and return the answer with cited sources.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "knowledge_base_id": {"type": "string", "format": "uuid"},
                "top_k": {"type": "integer", "default": 5},
                "llm_model": {"type": "string", "example": "claude-sonnet-4-6", "description": "Override default LLM model (optional)"},
                "system_prompt": {"type": "string", "description": "Override default system prompt (optional)"},
            },
            "required": ["query", "knowledge_base_id"],
        }
    },
    responses={
        200: OpenApiResponse(description="Answer with cited sources and token usage"),
        502: OpenApiResponse(description="LLM call failed"),
    },
    tags=["RAG"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def answer_view(request):
    query = request.data.get("query", "").strip()
    kb_id = request.data.get("knowledge_base_id")
    top_k = min(int(request.data.get("top_k", 5)), TOP_K_MAX)
    llm_model = request.data.get("llm_model")
    system_prompt = request.data.get("system_prompt")

    if not query or not kb_id:
        return Response({"error": "validation_error", "message": "query and knowledge_base_id are required"}, status=400)

    try:
        answer_svc = container.answer_service()
        result = answer_svc.answer(
            query=query,
            knowledge_base_id=kb_id,
            tenant_id=str(request.user.tenant_id),
            top_k=top_k,
            llm_model=llm_model,
            system_prompt=system_prompt,
            caller=str(request.user.id),
        )
    except Exception as e:
        logger.exception("answer_service error")
        return Response({"error": "llm_error", "message": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    return Response(result)


@extend_schema(
    summary="[Public] Build RAG prompt — no auth required",
    description="Same as `/rag/prompt/` but open to external systems without authentication. Caller must supply `tenant_id` in the request body.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "knowledge_base_id": {"type": "string", "format": "uuid"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Required — identifies the tenant"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query", "knowledge_base_id", "tenant_id"],
        }
    },
    responses={200: _PROMPT_RESPONSE_SCHEMA},
    tags=["Public"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def public_prompt_view(request):
    query = request.data.get("query", "").strip()
    kb_id = request.data.get("knowledge_base_id")
    tenant_id = request.data.get("tenant_id", "").strip()
    top_k = min(int(request.data.get("top_k", 5)), TOP_K_MAX)

    if not query or not kb_id:
        return Response({"error": "validation_error", "message": "query and knowledge_base_id are required"}, status=400)
    if not tenant_id:
        return Response({"error": "validation_error", "message": "tenant_id is required"}, status=400)

    return _build_prompt_response(query, kb_id, tenant_id, top_k, LOG_CALLER_EXTERNAL)
