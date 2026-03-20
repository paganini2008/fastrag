import { api } from "./baseApi";

export interface TenantSettings {
  embedding_model: string;
  llm_model: string;
}

export const settingsApi = api.injectEndpoints({
  endpoints: (build) => ({
    getSettings: build.query<TenantSettings, void>({
      query: () => "tenants/settings/",
      providesTags: ["Settings"],
    }),
    updateSettings: build.mutation<TenantSettings, Partial<TenantSettings>>({
      query: (body) => ({ url: "tenants/settings/", method: "PATCH", body }),
      invalidatesTags: ["Settings"],
    }),
  }),
});

export const { useGetSettingsQuery, useUpdateSettingsMutation } = settingsApi;
