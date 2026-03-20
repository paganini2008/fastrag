import { api } from "./baseApi";

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  kb_type: string;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  retrieval_top_k: number;
  is_active: boolean;
  doc_count: number;
  chunk_count: number;
  collection_name: string;
  rebuild_status: "idle" | "running" | "done" | "failed";
  rebuild_progress: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  page: number;
  page_size: number;
  results: T[];
}

export const knowledgeBaseApi = api.injectEndpoints({
  endpoints: (builder) => ({
    listKnowledgeBases: builder.query<PaginatedResponse<KnowledgeBase>, { page?: number; search?: string }>({
      query: (params) => ({ url: "knowledge-bases/", params }),
      providesTags: (result) =>
        result
          ? [...result.results.map(({ id }) => ({ type: "KnowledgeBase" as const, id })), "KnowledgeBase"]
          : ["KnowledgeBase"],
    }),
    getKnowledgeBase: builder.query<KnowledgeBase, string>({
      query: (id) => `knowledge-bases/${id}/`,
      providesTags: (_result, _err, id) => [{ type: "KnowledgeBase", id }],
    }),
    createKnowledgeBase: builder.mutation<KnowledgeBase, Partial<KnowledgeBase>>({
      query: (data) => ({ url: "knowledge-bases/", method: "POST", body: data }),
      invalidatesTags: ["KnowledgeBase"],
    }),
    updateKnowledgeBase: builder.mutation<KnowledgeBase, { id: string } & Partial<KnowledgeBase>>({
      query: ({ id, ...data }) => ({ url: `knowledge-bases/${id}/`, method: "PATCH", body: data }),
      invalidatesTags: ["KnowledgeBase"],
    }),
    deleteKnowledgeBase: builder.mutation<void, string>({
      query: (id) => ({ url: `knowledge-bases/${id}/`, method: "DELETE" }),
      invalidatesTags: ["KnowledgeBase"],
    }),
    rebuildKnowledgeBase: builder.mutation<KnowledgeBase, { id: string; embedding_model: string }>({
      query: ({ id, embedding_model }) => ({
        url: `knowledge-bases/${id}/rebuild/`,
        method: "POST",
        body: { embedding_model },
      }),
      invalidatesTags: (_result, _err, { id }) => [{ type: "KnowledgeBase", id }, "KnowledgeBase"],
    }),
  }),
});

export const {
  useListKnowledgeBasesQuery,
  useGetKnowledgeBaseQuery,
  useCreateKnowledgeBaseMutation,
  useUpdateKnowledgeBaseMutation,
  useDeleteKnowledgeBaseMutation,
  useRebuildKnowledgeBaseMutation,
} = knowledgeBaseApi;
