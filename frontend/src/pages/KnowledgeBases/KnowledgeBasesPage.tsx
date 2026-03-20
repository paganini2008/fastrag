import { useState, useEffect, useRef } from "react";
import { Table, Button, Modal, Form, Input, InputNumber, Select, Tag, Space, Popconfirm, Progress, Alert, App } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, FileOutlined, QuestionCircleOutlined, ReloadOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import {
  useListKnowledgeBasesQuery,
  useCreateKnowledgeBaseMutation,
  useUpdateKnowledgeBaseMutation,
  useDeleteKnowledgeBaseMutation,
  useRebuildKnowledgeBaseMutation,
} from "../../store/api/knowledgeBaseApi";
import type { KnowledgeBase } from "../../store/api/knowledgeBaseApi";
import { EMBEDDING_MODELS } from "../../constants/models";

export default function KnowledgeBasesPage() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeBase | null>(null);
  const [reindexTarget, setReindexTarget] = useState<KnowledgeBase | null>(null);
  const [reindexModel, setReindexModel] = useState("");
  const [form] = Form.useForm();

  const { data, isLoading, refetch } = useListKnowledgeBasesQuery({ page });
  const hasRunning = (data?.results ?? []).some((kb) => kb.rebuild_status === "running");
  const prevStatusRef = useRef<Record<string, string>>({});

  useEffect(() => {
    if (!hasRunning) return;
    const id = setInterval(refetch, 2000);
    return () => clearInterval(id);
  }, [hasRunning, refetch]);

  // Completion notifications: detect running → done/failed transitions
  useEffect(() => {
    if (!data?.results) return;
    data.results.forEach((kb) => {
      const prev = prevStatusRef.current[kb.id];
      if (prev === "running") {
        if (kb.rebuild_status === "done") {
          message.success(`"${kb.name}" reindex complete`);
        } else if (kb.rebuild_status === "failed") {
          message.error(`"${kb.name}" reindex failed`);
        }
      }
      prevStatusRef.current[kb.id] = kb.rebuild_status;
    });
  }, [data?.results, message]);

  const [createKB] = useCreateKnowledgeBaseMutation();
  const [updateKB] = useUpdateKnowledgeBaseMutation();
  const [deleteKB] = useDeleteKnowledgeBaseMutation();
  const [rebuildKB, { isLoading: isReindexing }] = useRebuildKnowledgeBaseMutation();

  const openCreate = () => { setEditing(null); form.resetFields(); setModalOpen(true); };
  const openEdit = (kb: KnowledgeBase) => {
    setEditing(kb);
    form.setFieldsValue({ name: kb.name, description: kb.description, kb_type: kb.kb_type, chunk_size: kb.chunk_size, chunk_overlap: kb.chunk_overlap, retrieval_top_k: kb.retrieval_top_k });
    setModalOpen(true);
  };

  const openReindex = (kb: KnowledgeBase) => {
    setReindexTarget(kb);
    setReindexModel(kb.embedding_model);
  };

  const handleSubmit = async () => {
    let values: any;
    try {
      values = await form.validateFields();
    } catch {
      return;
    }
    try {
      if (editing) {
        await updateKB({ id: editing.id, ...values }).unwrap();
        message.success("Updated");
      } else {
        await createKB(values).unwrap();
        message.success("Created");
      }
      setModalOpen(false);
    } catch (err: any) {
      const detail = err?.data?.message || err?.data?.detail || "Operation failed";
      message.error(detail);
    }
  };

  const handleReindex = async () => {
    if (!reindexTarget) return;
    try {
      await rebuildKB({ id: reindexTarget.id, embedding_model: reindexModel }).unwrap();
      message.info(`"${reindexTarget.name}" reindex started — results will appear when complete`);
      setReindexTarget(null);
    } catch (err: any) {
      message.error(err?.data?.detail || "Failed to start reindex");
    }
  };

  const modelChanged = !!(reindexTarget && reindexModel !== reindexTarget.embedding_model);

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string, r: KnowledgeBase) => (
        <div>
          <button
            className="text-indigo-400 hover:text-indigo-300 font-medium text-sm transition-colors"
            onClick={() => navigate(`/knowledge-bases/${r.id}/documents`)}
          >
            {name}
          </button>
          {r.rebuild_status === "running" && (
            <div className="mt-1.5 w-48">
              <Progress percent={r.rebuild_progress} size="small" strokeColor="#6366f1" status="active" />
              <span className="text-xs text-slate-500">Re-embedding…</span>
            </div>
          )}
          {r.rebuild_status === "done" && (
            <div className="mt-1"><Tag color="green" className="text-xs">Reindexed</Tag></div>
          )}
          {r.rebuild_status === "failed" && (
            <div className="mt-1"><Tag color="red" className="text-xs">Reindex failed</Tag></div>
          )}
        </div>
      ),
    },
    {
      title: "Type",
      dataIndex: "kb_type",
      key: "kb_type",
      width: 120,
      render: (v: string) => v ? <Tag className="text-xs">{v}</Tag> : <span className="text-slate-500 text-xs">—</span>,
    },
    {
      title: "Embedding Model",
      dataIndex: "embedding_model",
      key: "embedding_model",
      render: (m: string) => (
        <Tag className="text-xs font-mono" color="blue">{m}</Tag>
      ),
    },
    {
      title: "Docs",
      dataIndex: "doc_count",
      key: "doc_count",
      width: 70,
      render: (v: number) => <span className="text-slate-300 text-sm">{v}</span>,
    },
    {
      title: "Chunks",
      dataIndex: "chunk_count",
      key: "chunk_count",
      width: 90,
      render: (v: number) => <span className="text-slate-300 text-sm">{v}</span>,
    },
    {
      title: "Status",
      dataIndex: "is_active",
      key: "is_active",
      width: 90,
      render: (v: boolean) => (
        <Tag className={v ? "status-indexed" : "status-failed"} bordered>
          {v ? "Active" : "Inactive"}
        </Tag>
      ),
    },
    {
      title: "Actions",
      key: "actions",
      width: 260,
      render: (_: unknown, r: KnowledgeBase) => (
        <Space size="small">
          <Button icon={<FileOutlined />} size="small" onClick={() => navigate(`/knowledge-bases/${r.id}/documents`)}>
            Docs
          </Button>
          <Button icon={<QuestionCircleOutlined />} size="small" onClick={() => navigate(`/knowledge-bases/${r.id}/faq`)}>
            FAQ
          </Button>
          <Button
            icon={<ReloadOutlined />}
            size="small"
            onClick={() => openReindex(r)}
            disabled={r.rebuild_status === "running"}
            title="Reindex"
          >
            Reindex
          </Button>
          <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(r)} />
          <Popconfirm title="Delete this knowledge base?" onConfirm={() => deleteKB(r.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Knowledge Bases</h1>
          <p className="text-slate-400 text-sm mt-0.5">Manage your document collections and FAQ libraries</p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          New Knowledge Base
        </Button>
      </div>

      <div className="glass-card overflow-hidden">
        <Table
          columns={columns}
          dataSource={data?.results}
          rowKey="id"
          loading={isLoading}
          pagination={{
            total: data?.count,
            current: page,
            onChange: setPage,
            pageSize: 20,
          }}
        />
      </div>

      {/* Create / Edit modal */}
      <Modal
        title={<span className="text-white">{editing ? "Edit Knowledge Base" : "New Knowledge Base"}</span>}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText={editing ? "Save" : "Create"}
      >
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Product Documentation" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} placeholder="Optional description..." />
          </Form.Item>
          <Form.Item name="kb_type" label="Type">
            <Input placeholder="e.g. product, support, faq..." />
          </Form.Item>
          <div className="grid grid-cols-3 gap-4">
            <Form.Item name="chunk_size" label="Chunk Size" initialValue={512}>
              <InputNumber min={128} max={2048} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="chunk_overlap" label="Overlap" initialValue={64}>
              <InputNumber min={0} max={512} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="retrieval_top_k" label="Top-K" initialValue={5}>
              <InputNumber min={1} max={50} style={{ width: "100%" }} />
            </Form.Item>
          </div>
        </Form>
      </Modal>

      {/* Reindex modal */}
      <Modal
        title={<span className="text-white">Reindex — {reindexTarget?.name}</span>}
        open={!!reindexTarget}
        onOk={handleReindex}
        onCancel={() => setReindexTarget(null)}
        okText="Start Reindex"
        okButtonProps={{ loading: isReindexing, danger: modelChanged, disabled: !modelChanged }}
        width={480}
      >
        <div className="space-y-4 py-2">
          <div>
            <label className="text-slate-300 text-sm font-medium block mb-1.5">Embedding Model</label>
            <Select
              value={reindexModel}
              onChange={setReindexModel}
              options={EMBEDDING_MODELS}
              style={{ width: "100%" }}
            />
          </div>

          {modelChanged ? (
            <Alert
              type="warning"
              showIcon
              message="All documents will be re-embedded"
              description={
                <span className="text-xs">
                  Switching from <strong>{reindexTarget?.embedding_model}</strong> to <strong>{reindexModel}</strong>{" "}
                  requires re-embedding all {reindexTarget?.chunk_count} chunks. Retrieval will be unavailable during reindex.
                  This cannot be undone.
                </span>
              }
            />
          ) : (
            <Alert
              type="info"
              showIcon
              message="Select a different model to reindex"
            />
          )}
        </div>
      </Modal>
    </div>
  );
}
