import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import type { BaseQueryFn, FetchArgs, FetchBaseQueryError } from "@reduxjs/toolkit/query";
import type { RootState } from "../index";
import { setCredentials, logout } from "../slices/authSlice";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const baseQuery = fetchBaseQuery({
  baseUrl: `${BASE_URL}/api/v1/`,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.access;
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return headers;
  },
});

const baseQueryWithReauth: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (
  args,
  api,
  extraOptions,
) => {
  let result = await baseQuery(args, api, extraOptions);

  if (result.error?.status === 401) {
    const refresh = (api.getState() as RootState).auth.refresh;
    if (refresh) {
      const refreshResult = await baseQuery(
        { url: "auth/refresh/", method: "POST", body: { refresh } },
        api,
        extraOptions,
      );
      if (refreshResult.data) {
        const state = api.getState() as RootState;
        const data = refreshResult.data as { access: string };
        api.dispatch(setCredentials({ user: state.auth.user!, access: data.access, refresh }));
        result = await baseQuery(args, api, extraOptions);
      } else {
        api.dispatch(logout());
      }
    } else {
      api.dispatch(logout());
    }
  }

  return result;
};

export const api = createApi({
  reducerPath: "api",
  baseQuery: baseQueryWithReauth,
  tagTypes: ["KnowledgeBase", "Document", "DocumentContent", "FAQ", "Chunk", "Log", "Settings"],
  endpoints: () => ({}),
});
