import { api } from "./baseApi";
import type { PaginatedResponse } from "./knowledgeBaseApi";

export interface FAQItem {
  id: string;
  question: string;
  answer: string;
  tags: string[];
  is_active: boolean;
  is_embedded: boolean;
  created_at: string;
  updated_at: string;
}

export const faqApi = api.injectEndpoints({
  endpoints: (builder) => ({
    listFAQ: builder.query<PaginatedResponse<FAQItem>, { kbId: string; page?: number; search?: string }>({
      query: ({ kbId, ...params }) => ({ url: `knowledge-bases/${kbId}/faq/`, params }),
      providesTags: ["FAQ"],
    }),
    getFAQ: builder.query<FAQItem, { kbId: string; id: string }>({
      query: ({ kbId, id }) => `knowledge-bases/${kbId}/faq/${id}/`,
      providesTags: (_r, _e, { id }) => [{ type: "FAQ", id }],
    }),
    createFAQ: builder.mutation<FAQItem, { kbId: string; question: string; answer: string; tags?: string[] }>({
      query: ({ kbId, ...data }) => ({
        url: `knowledge-bases/${kbId}/faq/`,
        method: "POST",
        body: data,
      }),
      invalidatesTags: ["FAQ"],
    }),
    updateFAQ: builder.mutation<FAQItem, { kbId: string; id: string } & Partial<FAQItem>>({
      query: ({ kbId, id, ...data }) => ({
        url: `knowledge-bases/${kbId}/faq/${id}/`,
        method: "PATCH",
        body: data,
      }),
      invalidatesTags: ["FAQ"],
    }),
    deleteFAQ: builder.mutation<void, { kbId: string; id: string }>({
      query: ({ kbId, id }) => ({
        url: `knowledge-bases/${kbId}/faq/${id}/`,
        method: "DELETE",
      }),
      invalidatesTags: ["FAQ"],
    }),
    bulkImportFAQ: builder.mutation<{ created: number }, { kbId: string; items: Array<{ question: string; answer: string }> }>({
      query: ({ kbId, items }) => ({
        url: `knowledge-bases/${kbId}/faq/bulk-import/`,
        method: "POST",
        body: { items },
      }),
      invalidatesTags: ["FAQ"],
    }),
  }),
});

export const {
  useListFAQQuery,
  useGetFAQQuery,
  useCreateFAQMutation,
  useUpdateFAQMutation,
  useDeleteFAQMutation,
  useBulkImportFAQMutation,
} = faqApi;
