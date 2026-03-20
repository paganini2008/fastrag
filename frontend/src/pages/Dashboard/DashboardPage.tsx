import { Tag, Button, Table, Skeleton } from "antd";
import {
  BookOutlined, FileOutlined, SearchOutlined, RightOutlined,
  QuestionCircleOutlined, ThunderboltOutlined, ArrowUpOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useListKnowledgeBasesQuery } from "../../store/api/knowledgeBaseApi";
import type { KnowledgeBase } from "../../store/api/knowledgeBaseApi";
import { useAppSelector } from "../../store/hooks";

function StatCard({
  icon, label, value, color, onClick, trend,
}: {
  icon: React.ReactNode; label: string; value: number;
  color: string; onClick?: () => void; trend?: string;
}) {
  return (
    <div
      onClick={onClick}
      className={`glass-card p-5 ${onClick ? "cursor-pointer hover:scale-[1.02] transition-transform" : ""}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-widest font-medium mb-1">{label}</p>
          <p className="text-3xl font-bold text-white">{value.toLocaleString()}</p>
          {trend && (
            <p className="flex items-center gap-1 text-xs text-emerald-400 mt-1">
              <ArrowUpOutlined />
              {trend}
            </p>
          )}
        </div>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const user = useAppSelector((s) => s.auth.user);
  const { data, isLoading } = useListKnowledgeBasesQuery({});
  const kbs = data?.results ?? [];
  const totalDocs = kbs.reduce((s, kb) => s + kb.doc_count, 0);
  const totalChunks = kbs.reduce((s, kb) => s + kb.chunk_count, 0);

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string, r: KnowledgeBase) => (
        <button
          className="text-indigo-400 hover:text-indigo-300 font-medium text-sm transition-colors"
          onClick={() => navigate(`/knowledge-bases/${r.id}/documents`)}
        >
          {name}
        </button>
      ),
    },
    {
      title: "Docs",
      dataIndex: "doc_count",
      key: "doc_count",
      width: 80,
      render: (v: number) => <span className="text-slate-300 text-sm">{v}</span>,
    },
    {
      title: "Chunks",
      dataIndex: "chunk_count",
      key: "chunk_count",
      width: 100,
      render: (v: number) => <span className="text-slate-300 text-sm">{v}</span>,
    },
    {
      title: "Status",
      dataIndex: "is_active",
      key: "is_active",
      width: 100,
      render: (v: boolean) => (
        <Tag className={v ? "status-indexed" : "status-failed"} bordered>
          {v ? "Active" : "Inactive"}
        </Tag>
      ),
    },
    {
      title: "",
      key: "actions",
      width: 90,
      render: (_: unknown, r: KnowledgeBase) => (
        <Button
          size="small"
          icon={<RightOutlined />}
          onClick={() => navigate(`/knowledge-bases/${r.id}/documents`)}
        >
          Open
        </Button>
      ),
    },
  ];

  const quickActions = [
    {
      icon: <SearchOutlined className="text-indigo-400 text-xl" />,
      title: "Retrieval Test",
      desc: "Test your knowledge bases with natural language queries and full RAG answers.",
      path: "/retrieval",
      gradient: "from-indigo-500/10 to-purple-500/10",
      border: "border-indigo-500/20",
    },
    {
      icon: <QuestionCircleOutlined className="text-purple-400 text-xl" />,
      title: "FAQ Management",
      desc: "Add FAQ items to knowledge bases. They are auto-embedded and instantly searchable.",
      path: "/knowledge-bases",
      gradient: "from-purple-500/10 to-pink-500/10",
      border: "border-purple-500/20",
    },
    {
      icon: <ThunderboltOutlined className="text-amber-400 text-xl" />,
      title: "Ingestion Jobs",
      desc: "Monitor document processing jobs — parsing, chunking, and vector embedding status.",
      path: "/jobs",
      gradient: "from-amber-500/10 to-orange-500/10",
      border: "border-amber-500/20",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          Welcome back,{" "}
          <span className="gradient-text">{user?.username || "User"}</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Here's an overview of your RAG Platform.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass-card p-5">
              <Skeleton active paragraph={{ rows: 1 }} />
            </div>
          ))
        ) : (
          <>
            <StatCard
              icon={<BookOutlined />}
              label="Knowledge Bases"
              value={kbs.length}
              color="bg-indigo-500/15 text-indigo-400"
              onClick={() => navigate("/knowledge-bases")}
              trend="All active"
            />
            <StatCard
              icon={<FileOutlined />}
              label="Total Documents"
              value={totalDocs}
              color="bg-emerald-500/15 text-emerald-400"
            />
            <StatCard
              icon={<SearchOutlined />}
              label="Indexed Chunks"
              value={totalChunks}
              color="bg-amber-500/15 text-amber-400"
              onClick={() => navigate("/retrieval")}
            />
          </>
        )}
      </div>

      {/* KB Table */}
      <div className="glass-card overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#2a2a4a]">
          <h2 className="text-sm font-semibold text-white">Knowledge Bases</h2>
          <Button type="primary" size="small" onClick={() => navigate("/knowledge-bases")}>
            Manage
          </Button>
        </div>
        <Table
          columns={columns}
          dataSource={kbs}
          rowKey="id"
          loading={isLoading}
          pagination={false}
          size="small"
          locale={{ emptyText: "No knowledge bases yet. Create one to get started." }}
        />
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-3 gap-4">
        {quickActions.map((item) => (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`text-left p-5 rounded-xl border bg-gradient-to-br ${item.gradient} ${item.border}
              hover:scale-[1.02] transition-all duration-150`}
          >
            <div className="mb-3">{item.icon}</div>
            <h3 className="text-sm font-semibold text-white mb-1">{item.title}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
