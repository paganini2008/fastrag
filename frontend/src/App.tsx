import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Provider } from "react-redux";
import { ConfigProvider, App as AntApp } from "antd";
import { store } from "./store";
import { useAppSelector } from "./store/hooks";
import MainLayout from "./components/Layout/MainLayout";
import LoginPage from "./pages/Login/LoginPage";
import DashboardPage from "./pages/Dashboard/DashboardPage";
import KnowledgeBasesPage from "./pages/KnowledgeBases/KnowledgeBasesPage";
import DocumentsPage from "./pages/Documents/DocumentsPage";
import FAQPage from "./pages/FAQ/FAQPage";
import RetrievalTestPage from "./pages/Retrieval/RetrievalTestPage";
import LogsPage from "./pages/Logs/LogsPage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="knowledge-bases" element={<KnowledgeBasesPage />} />
        <Route path="knowledge-bases/:kbId/documents" element={<DocumentsPage />} />
        <Route path="knowledge-bases/:kbId/faq" element={<FAQPage />} />
        <Route path="retrieval" element={<RetrievalTestPage />} />
        <Route path="logs" element={<LogsPage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <Provider store={store}>
      <ConfigProvider theme={{ token: { colorPrimary: "#6366f1" } }}>
        <AntApp>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </AntApp>
      </ConfigProvider>
    </Provider>
  );
}
