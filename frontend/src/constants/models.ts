export const EMBEDDING_MODELS = [
  { value: "text-embedding-3-small", label: "text-embedding-3-small (1536d, fast)" },
  { value: "text-embedding-3-large", label: "text-embedding-3-large (3072d, best)" },
  { value: "text-embedding-ada-002", label: "text-embedding-ada-002 (legacy)" },
];

export const LLM_MODELS = [
  { value: "claude-sonnet-4-6", label: "Claude Sonnet 4.6" },
  { value: "claude-opus-4-6", label: "Claude Opus 4.6" },
  { value: "claude-haiku-4-5-20251001", label: "Claude Haiku 4.5" },
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini" },
];
