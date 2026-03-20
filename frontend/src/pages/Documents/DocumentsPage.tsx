import { useState, useEffect, useRef } from "react";
import { Table, Button, Upload, Modal, Input, Tag, Space, Popconfirm, App, Drawer, List, Select, Alert } from "antd";
import {
  UploadOutlined, LinkOutlined, ReloadOutlined,
  EyeOutlined, DeleteOutlined, FileOutlined, FileTextOutlined,
} from "@ant-design/icons";
import { useParams } from "react-router-dom";
import {
  useListDocumentsQuery, useUploadDocumentMutation, useImportUrlMutation,
  useDeleteDocumentMutation, useReindexDocumentMutation, useGetDocumentChunksQuery,
  useGetDocumentContentQuery,
} from "../../store/api/documentApi";
import type { Document, DocumentChunk } from "../../store/api/documentApi";

const PROCESSING_STATUSES = new Set(["pending", "parsing", "parsed", "chunking", "chunked", "embedding"]);

const STATUS_CLASSES: Record<string, string> = {
  pending: "status-pending",
  parsing: "status-processing",
  parsed: "status-processing",
  chunking: "status-processing",
  chunked: "status-processing",
  embedding: "status-processing",
  indexed: "status-indexed",
  failed: "status-failed",
};

function ContentModal({ kbId, docId, docName, onClose }: {
  kbId: string; docId: string; docName: string; onClose: () => void;
}) {
  const { data, isLoading } = useGetDocumentContentQuery({ kbId, docId });
  return (
    <Modal
      title={<span className="text-white"><FileTextOutlined className="mr-2" />{docName}</span>}
      open
      onCancel={onClose}
      footer={null}
      width={760}
    >
      {data?.truncated && (
        <Alert
          type="warning"
          showIcon
          className="mb-3"
          message={`Showing first ${data.text.length.toLocaleString()} of ${data.total_length.toLocaleString()} characters`}
        />
      )}
      <pre className="text-xs text-slate-300 bg-[#0f0f1a] rounded-lg p-4 leading-relaxed whitespace-pre-wrap break-words max-h-[60vh] overflow-y-auto m-0">
        {isLoading ? "Loading…" : (data?.text || "No content available — document may not have been parsed yet.")}
      </pre>
    </Modal>
  );
}

function ChunksDrawer({ kbId, docId, docName, onClose }: {
  kbId: string; docId: string; docName: string; onClose: () => void;
}) {
  const { data } = useGetDocumentChunksQuery({ kbId, docId });
  return (
    <Drawer
      title={<span className="text-white"><EyeOutlined className="mr-2" />{docName}</span>}
      open
      onClose={onClose}
      width={640}
    >
      <List
        dataSource={data?.results}
        renderItem={(chunk: DocumentChunk) => (
          <List.Item className="!border-[#2a2a4a]">
            <div className="w-full">
              <div className="flex items-center gap-2 mb-2">
                <Tag>#{chunk.chunk_index}</Tag>
                {chunk.page && <Tag>Page {chunk.page}</Tag>}
                <Tag className={chunk.is_embedded ? "status-indexed" : "status-pending"} bordered>
                  {chunk.is_embedded ? "Embedded" : "Pending"}
                </Tag>
              </div>
              <p className="text-xs text-slate-400 bg-[#0f0f1a] rounded-lg p-3 leading-relaxed font-mono">
                {chunk.text}
              </p>
            </div>
          </List.Item>
        )}
      />
    </Drawer>
  );
}

export default function DocumentsPage() {
  const { kbId } = useParams<{ kbId: string }>();
  const { notification, message } = App.useApp();
  const [page, setPage] = useState(1);
  const [urlModalOpen, setUrlModalOpen] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [renderMode, setRenderMode] = useState<"static" | "selenium">("static");
  const [chunksDoc, setChunksDoc] = useState<{ id: string; name: string } | null>(null);
  const [contentDoc, setContentDoc] = useState<{ id: string; name: string } | null>(null);

  // Poll every 3 s when any document is still in-progress
  const { data, isLoading, refetch } = useListDocumentsQuery({ kbId: kbId!, page });
  const hasProcessing = data?.results.some((d: Document) => PROCESSING_STATUSES.has(d.status)) ?? false;
  useListDocumentsQuery(
    { kbId: kbId!, page },
    { pollingInterval: hasProcessing ? 3000 : 0, skip: !kbId },
  );

  // Notify when a document transitions to indexed or failed
  const prevStatuses = useRef<Record<string, string>>({});
  useEffect(() => {
    if (!data?.results) return;
    for (const doc of data.results) {
      const prev = prevStatuses.current[doc.id];
      if (prev && prev !== doc.status) {
        if (doc.status === "indexed") {
          notification.success({
            message: "Indexing complete",
            description: `"${doc.name}" is ready to search (${doc.chunk_count} chunks).`,
            placement: "bottomRight",
          });
        } else if (doc.status === "failed") {
          notification.error({
            message: "Indexing failed",
            description: `"${doc.name}": ${doc.error_message || "unknown error"}`,
            placement: "bottomRight",
          });
        }
      }
      prevStatuses.current[doc.id] = doc.status;
    }
  }, [data, notification]);

  const [uploadDoc] = useUploadDocumentMutation();
  const [importUrl] = useImportUrlMutation();
  const [deleteDoc] = useDeleteDocumentMutation();
  const [reindex] = useReindexDocumentMutation();

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    try {
      await uploadDoc({ kbId: kbId!, formData }).unwrap();
      message.success("Upload started — processing in background");
    } catch {
      message.error("Upload failed");
    }
    return false;
  };

  const handleImportUrl = async () => {
    try {
      await importUrl({ kbId: kbId!, url: urlInput, render_mode: renderMode }).unwrap();
      message.success("URL import started");
      setUrlModalOpen(false);
      setUrlInput("");
      setRenderMode("static");
    } catch {
      message.error("URL import failed");
    }
  };

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string) => (
        <div className="flex items-center gap-2">
          <FileOutlined className="text-slate-500" />
          <span className="text-slate-200 text-sm font-medium">{name}</span>
        </div>
      ),
    },
    {
      title: "Type",
      dataIndex: "source_type",
      key: "source_type",
      width: 80,
      render: (t: string) => <Tag className="text-xs uppercase">{t}</Tag>,
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 110,
      render: (s: string) => (
        <Tag className={STATUS_CLASSES[s] ?? ""} bordered>{s}</Tag>
      ),
    },
    {
      title: "Chunks",
      dataIndex: "chunk_count",
      key: "chunk_count",
      width: 80,
      render: (v: number) => <span className="text-slate-300 text-sm">{v ?? 0}</span>,
    },
    {
      title: "Actions",
      key: "actions",
      width: 260,
      render: (_: unknown, r: Document) => (
        <Space size="small">
          <Button icon={<FileTextOutlined />} size="small" onClick={() => setContentDoc({ id: r.id, name: r.name })}>Content</Button>
          <Button icon={<EyeOutlined />} size="small" onClick={() => setChunksDoc({ id: r.id, name: r.name })}>Chunks</Button>
          <Button icon={<ReloadOutlined />} size="small" onClick={() => reindex({ kbId: kbId!, docId: r.id })}>Reindex</Button>
          <Popconfirm title="Delete this document?" onConfirm={() => deleteDoc({ kbId: kbId!, docId: r.id })}>
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
          <h1 className="text-xl font-bold text-white">Documents</h1>
          <p className="text-slate-400 text-sm mt-0.5">Upload files or import URLs to index into this knowledge base</p>
        </div>
        <Space>
          <Upload beforeUpload={handleUpload} showUploadList={false}>
            <Button icon={<UploadOutlined />}>Upload File</Button>
          </Upload>
          <Button icon={<LinkOutlined />} onClick={() => setUrlModalOpen(true)}>Import URL</Button>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Refresh</Button>
        </Space>
      </div>

      <div className="glass-card overflow-hidden">
        <Table
          columns={columns}
          dataSource={data?.results}
          rowKey="id"
          loading={isLoading}
          pagination={{ total: data?.count, current: page, onChange: setPage, pageSize: 20 }}
        />
      </div>

      <Modal
        title={<span className="text-white">Import URL</span>}
        open={urlModalOpen}
        onOk={handleImportUrl}
        onCancel={() => setUrlModalOpen(false)}
        okText="Import"
      >
        <div className="py-2 space-y-4">
          <div>
            <label className="text-slate-300 text-sm font-medium block mb-2">URL</label>
            <Input
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://..."
              size="large"
            />
          </div>
          <div>
            <label className="text-slate-300 text-sm font-medium block mb-2">Page Type</label>
            <Select
              value={renderMode}
              onChange={setRenderMode}
              size="large"
              className="w-full"
              options={[
                { value: "static", label: "Static — plain HTML (fast)" },
                { value: "selenium", label: "Dynamic — JS-rendered via Selenium" },
              ]}
            />
          </div>
        </div>
      </Modal>

      {contentDoc && (
        <ContentModal
          kbId={kbId!}
          docId={contentDoc.id}
          docName={contentDoc.name}
          onClose={() => setContentDoc(null)}
        />
      )}

      {chunksDoc && (
        <ChunksDrawer
          kbId={kbId!}
          docId={chunksDoc.id}
          docName={chunksDoc.name}
          onClose={() => setChunksDoc(null)}
        />
      )}
    </div>
  );
}
