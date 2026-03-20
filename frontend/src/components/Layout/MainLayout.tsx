import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Dropdown } from "antd";
import {
  DashboardOutlined, BookOutlined, SearchOutlined,
  FileTextOutlined, LogoutOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined,
} from "@ant-design/icons";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { logout } from "../../store/slices/authSlice";

const navItems = [
  { path: "/dashboard", icon: <DashboardOutlined />, label: "Dashboard" },
  { path: "/knowledge-bases", icon: <BookOutlined />, label: "Knowledge Bases" },
  { path: "/retrieval", icon: <SearchOutlined />, label: "Retrieval Test" },
  { path: "/logs", icon: <FileTextOutlined />, label: "System Logs" },
];

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.auth.user);
  const [collapsed, setCollapsed] = useState(false);
  const appName = import.meta.env.VITE_APP_NAME || "RAG Platform";

  const activeKey =
    navItems.find((item) => location.pathname.startsWith(item.path))?.path ??
    location.pathname;

  return (
    <div className="flex h-screen bg-[#0f0f1a] text-slate-200">
      {/* Sidebar */}
      <aside
        className={`flex flex-col fixed left-0 top-0 h-full z-50 transition-all duration-300 ease-in-out
          ${collapsed ? "w-16" : "w-56"}
          bg-[#1a1a2e] border-r border-[#2a2a4a]`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-[#2a2a4a]">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-indigo-500/30">
            R
          </div>
          {!collapsed && (
            <span className="font-bold text-sm tracking-wide text-white truncate">
              {appName}
            </span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = activeKey === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                title={collapsed ? item.label : undefined}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150
                  ${isActive
                    ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/25"
                    : "text-slate-400 hover:text-white hover:bg-[#16213e]"
                  }`}
              >
                <span className={`flex-shrink-0 text-base ${isActive ? "text-white" : ""}`}>
                  {item.icon}
                </span>
                {!collapsed && <span className="truncate">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Collapse toggle */}
        <div className="p-3 border-t border-[#2a2a4a]">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center py-2 rounded-lg text-slate-400 hover:text-white hover:bg-[#16213e] transition-colors"
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className={`flex flex-col flex-1 transition-all duration-300 ${collapsed ? "ml-16" : "ml-56"}`}>
        {/* Header */}
        <header className="sticky top-0 z-40 h-14 flex items-center justify-between px-6 bg-[#0f0f1a]/90 backdrop-blur-md border-b border-[#2a2a4a]">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 uppercase tracking-widest font-medium">
              {navItems.find(n => n.path === activeKey)?.label ?? "Dashboard"}
            </span>
          </div>

          <Dropdown
            menu={{
              items: [
                {
                  key: "email",
                  label: <span className="text-xs text-slate-400">{user?.email}</span>,
                  disabled: true,
                },
                { type: "divider" },
                {
                  key: "logout",
                  icon: <LogoutOutlined />,
                  label: "Sign out",
                  danger: true,
                  onClick: () => dispatch(logout()),
                },
              ],
            }}
            placement="bottomRight"
          >
            <button className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg hover:bg-[#16213e] transition-colors">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shadow shadow-indigo-500/30">
                {(user?.username || user?.email || "U")[0].toUpperCase()}
              </div>
              <span className="text-sm text-slate-300">{user?.username || user?.email}</span>
            </button>
          </Dropdown>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
