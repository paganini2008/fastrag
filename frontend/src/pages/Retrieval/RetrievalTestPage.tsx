import { useState } from "react";
import {
  Form, Input, InputNumber, Select, Button,
  Tag, Spin, Alert, Space,
} from "antd";
import { SearchOutlined, RobotOutlined, ThunderboltOutlined } from "@ant-design/icons";
import { useListKnowledgeBasesQuery } from "../../store/api/knowledgeBaseApi";
import { useSearchMutation, useGetAnswerMutation } from "../../store/api/retrievalApi";
import type { RetrievedChunk } from "../../store/api/retrievalApi";
import { LLM_MODELS } from "../../constants/models";

type TabMode = "search" | "answer";

export default function RetrievalTestPage() {
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState<TabMode>("search");
  const { data: kbs } = useListKnowledgeBasesQuery({});
  const [search, { isLoading: searching, data: searchResult }] = useSearchMutation();
  const [getAnswer, { isLoading: answering, data: answerResult, error: answerError }] = useGetAnswerMutation();

  const kbOptions = kbs?.results.map((kb) => ({ value: kb.id, label: kb.name })) ?? [];

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (activeTab === "search") {
      await search({
        query: values.query,
        knowledge_base_id: values.kb_id,
        top_k: values.top_k ?? 5,
        score_threshold: values.score_threshold ?? 0,
      });
    } else {
      await getAnswer({
        query: values.query,
        knowledge_base_id: values.kb_id,
        top_k: values.top_k ?? 5,
        llm_model: values.llm_model,
      });
    }
  };

  const tabs: { key: TabMode; icon: React.ReactNode; label: string }[] = [
    { key: "search", icon: <SearchOutlined />, label: "Vector Search" },
    { key: "answer", icon: <RobotOutlined />, label: "RAG Answer" },
  ];

  const isLoading = searching || answering;

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-white">Retrieval Test</h1>
        <p className="text-slate-400 text-sm mt-0.5">Test your knowledge bases with natural language queries</p>
      </div>

      {/* Query panel */}
      <div className="glass-card p-5">
        {/* Mode tabs */}
        <div className="flex gap-2 mb-5">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${activeTab === tab.key
                  ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/25"
                  : "text-slate-400 hover:text-white hover:bg-[#16213e]"
                }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        <Form form={form} layout="vertical" requiredMark={false}>
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="kb_id" label={<span className="text-slate-300 text-sm font-medium">Knowledge Base</span>} rules={[{ required: true }]} className="col-span-2">
              <Select options={kbOptions} placeholder="Select a knowledge base" size="large" />
            </Form.Item>

            <Form.Item name="query" label={<span className="text-slate-300 text-sm font-medium">Query</span>} rules={[{ required: true }]} className="col-span-2">
              <Input.TextArea
                rows={3}
                placeholder="Ask anything about your knowledge base..."
                size="large"
                className="font-medium"
              />
            </Form.Item>

            <Form.Item name="top_k" label={<span className="text-slate-300 text-sm font-medium">Top-K</span>} initialValue={5}>
              <InputNumber min={1} max={50} style={{ width: "100%" }} size="large" />
            </Form.Item>

            {activeTab === "search" ? (
              <Form.Item name="score_threshold" label={<span className="text-slate-300 text-sm font-medium">Min Score</span>} initialValue={0}>
                <InputNumber min={0} max={1} step={0.05} style={{ width: "100%" }} size="large" />
              </Form.Item>
            ) : (
              <Form.Item name="llm_model" label={<span className="text-slate-300 text-sm font-medium">LLM Model</span>} initialValue="gpt-4o-mini">
                <Select size="large" options={LLM_MODELS} />
              </Form.Item>
            )}
          </div>

          <Button
            type="primary"
            size="large"
            icon={activeTab === "search" ? <SearchOutlined /> : <ThunderboltOutlined />}
            loading={isLoading}
            onClick={handleSubmit}
            className="mt-1"
          >
            {activeTab === "search" ? "Search" : "Generate Answer"}
          </Button>
        </Form>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <Spin size="large" />
        </div>
      )}

      {/* Search results */}
      {searchResult && !searching && (
        <div className="glass-card overflow-hidden">
          <div className="px-5 py-4 border-b border-[#2a2a4a] flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">
              {searchResult.total} chunks found
            </h2>
            <Tag className="status-processing" bordered>
              {searchResult.latency_ms}ms
            </Tag>
          </div>

          {searchResult.chunks.length === 0 ? (
            <div className="p-8">
              <Alert message="No results found. Try a different query or lower the score threshold." type="info" />
            </div>
          ) : (
            <div className="divide-y divide-[#1e1e3a]">
              {searchResult.chunks.map((chunk: RetrievedChunk, i: number) => (
                <div key={chunk.id} className="p-5">
                  <div className="flex items-center gap-2 mb-3 flex-wrap">
                    <span className="w-6 h-6 rounded-full bg-indigo-600/20 text-indigo-400 text-xs font-bold flex items-center justify-center">
                      {i + 1}
                    </span>
                    <Tag className="status-indexed font-mono text-xs" bordered>
                      {chunk.score.toFixed(4)}
                    </Tag>
                    <Tag className="text-xs">{chunk.source.type}</Tag>
                    <span className="text-xs text-slate-500">
                      {chunk.source.name}{chunk.source.page ? ` · page ${chunk.source.page}` : ""}
                    </span>
                  </div>
                  <p className="text-sm text-slate-300 bg-[#0f0f1a] rounded-lg p-4 leading-relaxed font-mono">
                    {chunk.text}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* RAG Answer */}
      {answerResult && !answering && (
        <div className="glass-card overflow-hidden">
          <div className="px-5 py-4 border-b border-[#2a2a4a] flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <RobotOutlined className="text-indigo-400" />
              RAG Answer
            </h2>
            <Space>
              <Tag className="text-xs" bordered>Tokens: {answerResult.usage?.total_tokens}</Tag>
              <Tag className="status-processing" bordered>{answerResult.latency_ms}ms</Tag>
            </Space>
          </div>

          <div className="p-5 space-y-5">
            <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
              <p className="text-slate-200 leading-relaxed text-sm">{answerResult.answer}</p>
            </div>

            <div>
              <p className="text-xs text-slate-500 uppercase tracking-widest font-medium mb-3">Sources</p>
              <div className="space-y-2">
                {answerResult.sources.map((s: any, i: number) => (
                  <div key={i} className="flex items-center gap-3 text-xs p-2.5 rounded-lg bg-[#16213e]">
                    <span className="w-5 h-5 rounded bg-indigo-600/30 text-indigo-400 font-bold flex items-center justify-center text-[10px]">
                      {i + 1}
                    </span>
                    <span className="text-slate-300 flex-1">{s.source}</span>
                    <span className="text-slate-500 font-mono">{s.score?.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {answerError && (
        <Alert
          type="error"
          message="LLM Error"
          description={JSON.stringify(answerError)}
        />
      )}
    </div>
  );
}
