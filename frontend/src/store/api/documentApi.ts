import { api } from "./baseApi";
import type { PaginatedResponse } from "./knowledgeBaseApi";

export interface Document {
  id: string;
  name: string;
  source_type: "file" | "url" | "faq";
  mime_type: string;
  file_size: number;
  source_url: string;
  status: "pending" | "parsing" | "parsed" | "chunking" | "chunked" | "embedding" | "indexed" | "failed";
  error_message: string;
  page_count: number;
  chunk_count: number;
  word_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentContent {
  text: string;
  truncated: boolean;
  total_length: number;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  text: string;
  page: number;
  section: string;
  token_count: number;
  is_embedded: boolean;
}

export const documentApi = api.injectEndpoints({
  endpoints: (builder) => ({
    listDocuments: builder.query<PaginatedResponse<Document>, { kbId: string; page?: number; status?: string; search?: string }>({
      query: ({ kbId, ...params }) => ({ url: `knowledge-bases/${kbId}/documents/`, params }),
      providesTags: ["Document"],
    }),
    uploadDocument: builder.mutation<Document, { kbId: string; formData: FormData }>({
      query: ({ kbId, formData }) => ({
        url: `knowledge-bases/${kbId}/documents/upload/`,
        method: "POST",
        body: formData,
      }),
      invalidatesTags: ["Document", "KnowledgeBase"],
    }),
    importUrl: builder.mutation<Document, { kbId: string; url: string; render_mode?: string; name?: string }>({
      query: ({ kbId, ...data }) => ({
        url: `knowledge-bases/${kbId}/documents/import-url/`,
        method: "POST",
        body: data,
      }),
      invalidatesTags: ["Document"],
    }),
    deleteDocument: builder.mutation<void, { kbId: string; docId: string }>({
      query: ({ kbId, docId }) => ({
        url: `knowledge-bases/${kbId}/documents/${docId}/`,
        method: "DELETE",
      }),
      invalidatesTags: ["Document", "KnowledgeBase"],
    }),
    reindexDocument: builder.mutation<void, { kbId: string; docId: string }>({
      query: ({ kbId, docId }) => ({
        url: `knowledge-bases/${kbId}/documents/${docId}/reindex/`,
        method: "POST",
      }),
      invalidatesTags: ["Document", "DocumentContent"],
    }),
    getDocumentChunks: builder.query<PaginatedResponse<DocumentChunk>, { kbId: string; docId: string; page?: number }>({
      query: ({ kbId, docId, ...params }) => ({ url: `knowledge-bases/${kbId}/documents/${docId}/chunks/`, params }),
      providesTags: ["Chunk"],
    }),
    getDocumentContent: builder.query<DocumentContent, { kbId: string; docId: string }>({
      query: ({ kbId, docId }) => `knowledge-bases/${kbId}/documents/${docId}/content/`,
      providesTags: (_result, _err, { docId }) => [{ type: "DocumentContent", id: docId }],
    }),
  }),
});

export const {
  useListDocumentsQuery,
  useUploadDocumentMutation,
  useImportUrlMutation,
  useDeleteDocumentMutation,
  useReindexDocumentMutation,
  useGetDocumentChunksQuery,
  useGetDocumentContentQuery,
} = documentApi;
