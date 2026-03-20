import { api } from "./baseApi";

export interface RetrievedChunk {
  id: string;
  text: string;
  score: number;
  source: {
    type: string;
    name: string;
    document_id: string;
    page: number | null;
    url: string | null;
  };
  metadata: {
    chunk_index: number;
    knowledge_base_id: string;
    embedding_model: string;
  };
}

export interface SearchResponse {
  query: string;
  total: number;
  latency_ms: number;
  chunks: RetrievedChunk[];
}

export interface AnswerResponse {
  query: string;
  answer: string;
  sources: Array<{ text: string; score: number; source: string }>;
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  latency_ms: number;
}

export const retrievalApi = api.injectEndpoints({
  endpoints: (builder) => ({
    search: builder.mutation<SearchResponse, {
      query: string;
      knowledge_base_id: string;
      top_k?: number;
      score_threshold?: number;
      filters?: Record<string, unknown>;
    }>({
      query: (data) => ({ url: "retrieval/search/", method: "POST", body: data }),
    }),
    getAnswer: builder.mutation<AnswerResponse, {
      query: string;
      knowledge_base_id: string;
      top_k?: number;
      llm_model?: string;
    }>({
      query: (data) => ({ url: "rag/answer/", method: "POST", body: data }),
    }),
  }),
});

export const { useSearchMutation, useGetAnswerMutation } = retrievalApi;
