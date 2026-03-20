import { useEffect } from "react";
import { Form, Select, Button, App } from "antd";
import { useGetSettingsQuery, useUpdateSettingsMutation } from "../../store/api/settingsApi";
import { EMBEDDING_MODELS, LLM_MODELS } from "../../constants/models";

export default function SettingsPage() {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const { data, isLoading } = useGetSettingsQuery();
  const [updateSettings, { isLoading: isSaving }] = useUpdateSettingsMutation();

  useEffect(() => {
    if (data) form.setFieldsValue(data);
  }, [data, form]);

  const handleSave = async () => {
    let values;
    try {
      values = await form.validateFields();
    } catch {
      return;
    }
    try {
      await updateSettings(values).unwrap();
      message.success("Settings saved");
    } catch {
      message.error("Failed to save settings");
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 text-sm mt-0.5">Global defaults applied to all knowledge bases</p>
      </div>

      <div className="glass-card p-6 max-w-lg">
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item
            name="embedding_model"
            label="Default Embedding Model"
            extra={<span className="text-slate-500 text-xs">Used when creating new knowledge bases and during ingestion</span>}
          >
            <Select options={EMBEDDING_MODELS} loading={isLoading} />
          </Form.Item>

          <Form.Item
            name="llm_model"
            label="Default LLM Model"
            extra={<span className="text-slate-500 text-xs">Used for RAG answer generation when no model is specified</span>}
          >
            <Select options={LLM_MODELS} loading={isLoading} />
          </Form.Item>

          <Button type="primary" onClick={handleSave} loading={isSaving}>
            Save Settings
          </Button>
        </Form>
      </div>
    </div>
  );
}
