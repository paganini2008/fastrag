import { useState } from "react";
import { Table, Button, Modal, Form, Input, Tag, Space, Popconfirm, message } from "antd";
import {
  PlusOutlined, DeleteOutlined, EditOutlined,
  CheckCircleOutlined, ClockCircleOutlined,
} from "@ant-design/icons";
import { useParams } from "react-router-dom";
import {
  useListFAQQuery, useCreateFAQMutation, useUpdateFAQMutation,
  useDeleteFAQMutation,
} from "../../store/api/faqApi";
import type { FAQItem } from "../../store/api/faqApi";

export default function FAQPage() {
  const { kbId } = useParams<{ kbId: string }>();
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<FAQItem | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useListFAQQuery({ kbId: kbId!, page });
  const [createFAQ] = useCreateFAQMutation();
  const [updateFAQ] = useUpdateFAQMutation();
  const [deleteFAQ] = useDeleteFAQMutation();

  const openCreate = () => { setEditing(null); form.resetFields(); setModalOpen(true); };
  const openEdit = (item: FAQItem) => { setEditing(item); form.setFieldsValue(item); setModalOpen(true); };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editing) {
        await updateFAQ({ kbId: kbId!, id: editing.id, ...values }).unwrap();
        message.success("Updated");
      } else {
        await createFAQ({ kbId: kbId!, ...values }).unwrap();
        message.success("FAQ created — embedding started");
      }
      setModalOpen(false);
    } catch {
      message.error("Operation failed");
    }
  };

  const columns = [
    {
      title: "Question",
      dataIndex: "question",
      key: "question",
      render: (q: string) => (
        <span className="text-slate-200 font-medium text-sm">{q}</span>
      ),
    },
    {
      title: "Answer",
      dataIndex: "answer",
      key: "answer",
      ellipsis: true,
      render: (a: string) => (
        <span className="text-slate-400 text-xs leading-relaxed">{a}</span>
      ),
    },
    {
      title: "Embed",
      dataIndex: "is_embedded",
      key: "is_embedded",
      width: 110,
      render: (v: boolean) => v ? (
        <Tag icon={<CheckCircleOutlined />} className="status-indexed" bordered>Embedded</Tag>
      ) : (
        <Tag icon={<ClockCircleOutlined />} className="status-processing" bordered>Pending</Tag>
      ),
    },
    {
      title: "Active",
      dataIndex: "is_active",
      key: "is_active",
      width: 80,
      render: (v: boolean) => (
        <Tag className={v ? "status-indexed" : "status-failed"} bordered>{v ? "Yes" : "No"}</Tag>
      ),
    },
    {
      title: "",
      key: "actions",
      width: 90,
      render: (_: unknown, r: FAQItem) => (
        <Space size="small">
          <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(r)} />
          <Popconfirm title="Delete this FAQ item?" onConfirm={() => deleteFAQ({ kbId: kbId!, id: r.id })}>
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
          <h1 className="text-xl font-bold text-white">FAQ Items</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {data?.count ?? 0} items · Auto-embedded and searchable via RAG
          </p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Add FAQ
        </Button>
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
        title={<span className="text-white">{editing ? "Edit FAQ Item" : "New FAQ Item"}</span>}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={640}
        okText={editing ? "Save" : "Create"}
      >
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item
            name="question"
            label={<span className="text-slate-300 text-sm">Question</span>}
            rules={[{ required: true, message: "Question is required" }]}
          >
            <Input.TextArea rows={3} placeholder="What is your question?" />
          </Form.Item>
          <Form.Item
            name="answer"
            label={<span className="text-slate-300 text-sm">Answer</span>}
            rules={[{ required: true, message: "Answer is required" }]}
          >
            <Input.TextArea rows={5} placeholder="Provide a detailed answer..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
