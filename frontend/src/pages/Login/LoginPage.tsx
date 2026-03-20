import { Form, Input, Button, message } from "antd";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { setCredentials } from "../../store/slices/authSlice";

export default function LoginPage() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const appName = import.meta.env.VITE_APP_NAME || "RAG Platform";

  const onFinish = async (values: { email: string; password: string }) => {
    try {
      const resp = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/v1/auth/login/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(values),
        }
      );
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.message || "Login failed");
      dispatch(setCredentials({ user: data.user, access: data.access, refresh: data.refresh }));
      navigate("/dashboard");
    } catch (err: any) {
      message.error(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f0f1a] relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/5 rounded-full blur-3xl" />
      </div>

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(99,102,241,0.5) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99,102,241,0.5) 1px, transparent 1px)`,
          backgroundSize: "40px 40px",
        }}
      />

      {/* Card */}
      <div className="relative w-full max-w-md px-4">
        <div className="glass-card p-8 shadow-2xl shadow-black/50">
          {/* Logo */}
          <div className="flex flex-col items-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold mb-4 shadow-xl shadow-indigo-500/30">
              R
            </div>
            <h1 className="text-2xl font-bold text-white">{appName}</h1>
            <p className="text-slate-400 text-sm mt-1">Sign in to your account</p>
          </div>

          <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
            <Form.Item
              name="email"
              label={<span className="text-slate-300 text-sm font-medium">Email</span>}
              rules={[{ required: true, type: "email", message: "Valid email required" }]}
            >
              <Input
                size="large"
                placeholder="you@example.com"
                className="!bg-[#16213e] !border-[#2a2a4a] !text-white"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label={<span className="text-slate-300 text-sm font-medium">Password</span>}
              rules={[{ required: true, message: "Password required" }]}
            >
              <Input.Password
                size="large"
                placeholder="••••••••"
                className="!bg-[#16213e] !border-[#2a2a4a] !text-white"
              />
            </Form.Item>

            <Form.Item className="mb-0 mt-6">
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                block
                className="h-11 font-semibold text-sm"
              >
                Sign In
              </Button>
            </Form.Item>
          </Form>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          RAG Platform — Multi-tenant Knowledge Management
        </p>
      </div>
    </div>
  );
}
