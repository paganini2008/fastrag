# RAG Platform — 项目文档

> 多租户检索增强生成（Retrieval-Augmented Generation）平台，支持文档管理、向量检索、LLM 问答与 FAQ 知识库。

---

## 目录

1. [项目概览](#1-项目概览)
2. [技术选型](#2-技术选型)
3. [项目结构](#3-项目结构)
4. [后端模块详解](#4-后端模块详解)
5. [前端模块详解](#5-前端模块详解)
6. [数据流与前后端交互](#6-数据流与前后端交互)
7. [核心 RAG 流程](#7-核心-rag-流程)
8. [API 接口总览](#8-api-接口总览)
9. [配置说明](#9-配置说明)
10. [环境搭建与启动](#10-环境搭建与启动)
11. [运行测试](#11-运行测试)
12. [Docker 部署](#12-docker-部署)

---

## 1. 项目概览

RAG Platform 是一个生产级多租户知识管理与 AI 问答平台。核心能力：

| 能力 | 说明 |
|------|------|
| **多租户隔离** | 所有数据库表和 Qdrant 向量均携带 `tenant_id`，数据严格隔离 |
| **文档知识库** | 支持 PDF / DOCX / XLSX / PPTX / TXT / HTML / MD 等格式上传，也支持 URL 抓取 |
| **异步处理流水线** | 文件上传后自动触发 Celery 任务：解析 → 分块 → 嵌入 → 写入向量库 |
| **向量检索** | 基于 Qdrant 的余弦相似度检索，返回最相关文档片段及评分 |
| **RAG 问答** | 检索上下文后调用 OpenAI / Anthropic LLM 生成完整答案 |
| **FAQ 知识库** | 手动维护问答对，自动向量化，与文档检索统一入口 |
| **知识库重建** | 每个知识库可独立切换嵌入模型，异步重建向量索引，实时进度追踪 |
| **Swagger 文档** | 内置 OpenAPI 3.0 文档，访问 `/api/schema/swagger-ui/` |
| **审计日志** | 自动记录每次检索和 RAG 问答的入参、耗时、Token 用量 |

---

## 2. 技术选型

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.13 | 运行环境 |
| **uv** | latest | 包管理器（替代 pip/poetry），极速依赖解析 |
| **Django** | 6.x | Web 框架，ORM，Admin |
| **Django REST Framework** | 3.16 | RESTful API 构建 |
| **djangorestframework-simplejwt** | 5.x | JWT 认证，支持 Token Blacklist |
| **drf-spectacular** | 0.29 | 自动生成 OpenAPI 3.0 / Swagger 文档 |
| **Celery** | 5.x | 分布式异步任务队列 |
| **Redis** | 7.x | Celery Broker + Result Backend |
| **PostgreSQL** | 15+ | 主数据库，schema `rag` 做命名空间隔离 |
| **Qdrant** | 1.17 | 高性能向量数据库，cosine 相似度检索 |
| **MinIO** | S3-compatible | 对象存储，存储原始上传文件 |
| **LlamaIndex** | 0.12+ | 文本分块（SentenceSplitter / SemanticSplitter） |
| **OpenAI SDK** | 2.x | 文本嵌入（text-embedding-3-small / 3-large）+ GPT 问答 |
| **Anthropic SDK** | 0.84 | Claude 系列 LLM 问答 |
| **python-decouple** | 3.8 | 从 `.env` 文件读取配置 |
| **django-cors-headers** | 4.x | 跨域请求处理 |
| **django-filter** | 25.x | DRF 过滤器支持 |
| **pypdf / python-docx / openpyxl / python-pptx** | — | 多格式文档解析 |
| **BeautifulSoup4 + playwright** | — | URL 网页抓取（静态/动态） |
| **tiktoken** | 0.12 | Token 计数（Prompt 构建） |
| **psycopg2-binary** | 2.9 | PostgreSQL 驱动 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| **React** | 19 | UI 框架 |
| **TypeScript** | 5.9 | 类型安全 |
| **Vite** | 7.x | 构建工具，开发服务器，API 代理 |
| **Redux Toolkit** | 2.x | 全局状态管理 |
| **RTK Query** | — | API 数据请求、缓存、自动 re-fetch |
| **React Router** | 7.x | 客户端路由 |
| **Ant Design** | 6.x | 组件库（表格、弹窗、表单、上传） |
| **Tailwind CSS** | 4.x | 原子化 CSS，暗色主题定制 |
| **@tailwindcss/vite** | — | Tailwind v4 Vite 插件集成 |

### 测试

| 技术 | 用途 |
|------|------|
| **pytest** | 测试框架 |
| **pytest-django** | Django 集成（DB、URL、客户端） |
| **pytest-mock** | Mock/Patch 支持 |
| **factory-boy** | 数据工厂（可选） |
| **APIClient** | DRF 测试客户端 |

---

## 3. 项目结构

```
rag/
├── backend/                    # Django 后端
│   ├── .env                    # 所有配置（不提交到版本库）
│   ├── pyproject.toml          # uv 依赖声明
│   ├── uv.lock                 # 锁定依赖版本
│   ├── pytest.ini              # pytest 配置
│   └── src/
│       ├── manage.py
│       ├── config/             # Django 项目配置
│       │   ├── settings/
│       │   │   ├── base.py     # 通用设置（读取 .env）
│       │   │   ├── development.py
│       │   │   └── production.py
│       │   ├── api_router.py   # /api/v1/ 路由总线
│       │   ├── celery.py       # Celery 应用初始化
│       │   ├── urls.py         # 根路由
│       │   └── wsgi.py / asgi.py
│       ├── apps/
│       │   ├── common/         # 公共基础（BaseModel、分页、存储、异常）
│       │   ├── tenants/        # 租户模型 + TenantMiddleware
│       │   ├── accounts/       # 用户认证（JWT + API Key）
│       │   ├── knowledge_bases/# 知识库 CRUD
│       │   ├── documents/      # 文档上传、URL 导入、分块预览
│       │   ├── faq/            # FAQ 管理、批量导入
│       │   ├── ingestion/      # Celery 任务编排（流水线入口）
│       │   ├── parsers/        # 文档解析（PDF/DOCX/XLSX/PPTX/TXT/HTML）
│       │   ├── chunking/       # 文本分块（LlamaIndex SentenceSplitter / SemanticSplitter）
│       │   ├── embeddings/     # OpenAI 嵌入调用（constants.py 共享 MODEL_DIMENSIONS）
│       │   ├── vector_store/   # Qdrant 封装（upsert / search / delete）
│       │   ├── retrieval/      # 检索、Prompt 构建、RAG 问答
│       │   └── audit/          # 检索日志、问答日志
│       └── tests/
│           ├── conftest.py     # Fixtures（tenant、user、auth_client、knowledge_base）
│           ├── test_auth.py
│           ├── test_knowledge_bases.py
│           ├── test_documents.py
│           ├── test_faq.py
│           └── test_retrieval.py
│
├── frontend/                   # React 前端
│   ├── .env                    # VITE_API_URL、VITE_APP_NAME
│   ├── package.json
│   ├── vite.config.ts          # 构建配置 + API 代理
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx            # 应用入口
│       ├── App.tsx             # 路由定义
│       ├── index.css           # Tailwind + Ant Design 暗色主题
│       ├── components/
│       │   └── Layout/
│       │       └── MainLayout.tsx  # 侧边栏 + Header + Outlet
│       ├── pages/
│       │   ├── Login/          # 登录页
│       │   ├── Dashboard/      # 总览（统计卡片 + KB 列表）
│       │   ├── KnowledgeBases/ # 知识库管理
│       │   ├── Documents/      # 文档管理 + 分块预览
│       │   ├── FAQ/            # FAQ 管理
│       │   ├── Retrieval/      # 向量检索 + RAG 问答测试
│       │   ├── Jobs/           # 摄取任务监控
│       │   └── Logs/           # 检索日志 + 问答日志
│       ├── store/
│       │   ├── index.ts        # Redux Store
│       │   ├── hooks.ts        # useAppDispatch / useAppSelector
│       │   ├── slices/
│       │   │   └── authSlice.ts   # 登录态（JWT tokens + user）
│       │   └── api/
│       │       ├── baseApi.ts     # RTK Query base（JWT header）
│       │       ├── knowledgeBaseApi.ts
│       │       ├── documentApi.ts
│       │       ├── faqApi.ts
│       │       └── retrievalApi.ts
│       └── types/
│           └── index.ts        # 统一类型导出
│
└── docs/
    └── README.md               # 本文档
```

---

## 4. 后端模块详解

### `config/`

| 文件 | 说明 |
|------|------|
| `settings/base.py` | 核心配置：读取 `.env`，注册 13 个 LOCAL_APPS，配置 JWT、CORS、Celery、MinIO、Qdrant、OpenAPI |
| `settings/development.py` | 开发环境：`DEBUG=True`，宽松 CORS |
| `settings/production.py` | 生产环境：`DEBUG=False`，严格 ALLOWED_HOSTS |
| `api_router.py` | 挂载所有子应用路由到 `/api/v1/` |
| `celery.py` | 创建 Celery 实例，自动发现 `tasks.py` |
| `urls.py` | 根路由：`/api/v1/`、`/api/schema/`（Swagger）、`/admin/` |

### `apps/common/`

平台公共基础，被所有其他 App 继承或引用。

| 文件 | 说明 |
|------|------|
| `models.py` | `UUIDModel`（UUID 主键）、`TenantScopedModel`（含 `tenant_id`、`created_at`、`updated_at`） |
| `storage.py` | `MinIOClient` 封装：`put_object` / `get_object` / `delete_object`；全局单例 `minio_client` |
| `pagination.py` | `StandardPagination`：`page_size=20`，返回 `{count, next, previous, results}` |
| `exceptions.py` | `custom_exception_handler`：统一错误格式 `{error, message, detail}` |

### `apps/tenants/`

多租户核心。

| 文件 | 说明 |
|------|------|
| `models.py` | `Tenant`：`name`、`slug`、`is_active`、`plan`、`settings`（JSONField，存储全局配置） |
| `middleware.py` | `TenantMiddleware`：从 JWT 中读取 `user.tenant_id`，挂载到 `request.tenant`；所有业务操作自动感知租户 |
| `views.py` | `TenantSettingsView`：`GET/PATCH /api/v1/tenants/settings/`，管理 `embedding_model`、`llm_model` 等租户级默认值 |

### `apps/accounts/`

认证与用户管理。

| 文件 | 说明 |
|------|------|
| `models.py` | `User`（AbstractBaseUser）：email 登录，含 `tenant_id`、`role`（owner/admin/member） |
| `authentication.py` | `APIKeyAuthentication`：通过 `X-API-Key` 头进行 Agent 调用认证 |
| `serializers.py` | `CustomTokenObtainPairSerializer`：JWT payload 注入 `tenant_id`、`role` |
| `views.py` | 登录（`/auth/login/`）、刷新 Token、注册、用户信息 |

### `apps/knowledge_bases/`

知识库管理，是所有文档和 FAQ 的容器。

**核心字段**：`name`、`description`、`embedding_model`、`chunk_size`（默认 512）、`chunk_overlap`（默认 64）、`retrieval_top_k`、`doc_count`、`chunk_count`

**重建字段**（重建嵌入模型时更新）：
- `collection_name`：重建后指向专属 Qdrant collection（`{QDRANT_COLLECTION}_kb_{kb_id_hex}`）；空字符串表示使用共享 collection
- `rebuild_status`：`idle` / `running` / `done` / `failed`
- `rebuild_progress`：0–100，用于前端进度条展示

所有文档/FAQ 均通过 `knowledge_base_id` + `tenant_id` 双重隔离。

### `apps/documents/`

文档生命周期管理。

| 文件 | 说明 |
|------|------|
| `models.py` | `Document`：记录文件元数据、状态机（pending→parsing→parsed→chunking→chunked→embedding→indexed/failed）、`file_path`（MinIO key）；`DocumentChunk`：分块文本、嵌入状态、向量 ID；`URLSource`：URL 抓取配置 |
| `views.py` | `upload`：接收文件 → 写入 MinIO → 触发 Celery；`import_url`：保存 URL → 触发 Celery；`chunks`：分块预览；`reindex`：重新触发流水线 |

MinIO 存储路径规则：`raw/{tenant_id}/{document_id}/file{.ext}`

### `apps/faq/`

FAQ 问答对管理。

**字段**：`question`、`answer`、`tags`（数组）、`is_active`、`is_embedded`

创建后自动触发 `embed_faq_item.delay(faq_id)` Celery 任务进行向量化。

**批量导入**：`POST /knowledge-bases/{kbId}/faq/bulk-import/`，接收 `{items: [{question, answer}]}` 批量创建。

### `apps/ingestion/`

Celery 异步任务编排层（流水线入口）。

```
ingest_document(document_id)
    ├── _parse_document()   → 调用 parsers.service，状态: parsing → parsed
    ├── _chunk_document()   → 调用 chunking.service，状态: chunking → chunked
    └── _embed_document()   → 调用 embeddings.service + vector_store.service，状态: embedding → indexed

ingest_url(document_id, url_source_id)
    ├── 抓取网页（static: requests / playwright / selenium）
    └── 走 ingest_document 相同流水线

embed_faq_item(faq_item_id)
    └── 嵌入 question+answer → 写入 Qdrant（source_type=faq）

rebuild_knowledge_base(kb_id, new_embedding_model)
    ├── 删除旧 per-KB collection（如有）
    ├── 从共享 collection 删除旧向量
    ├── 创建新 per-KB collection（维度匹配新模型）
    ├── 从 DB 读取所有 DocumentChunk 文本（跳过重解析/重分块）
    ├── 批量重嵌入（每批 100 条），每 5 个文档更新一次进度
    └── 更新 KB：embedding_model、vector_size、collection_name、rebuild_status=done
```

> 任务调度使用 `ThreadPoolExecutor`（无需外部 Broker），通过 `run_async(fn, *args)` 提交后台任务。

### `apps/parsers/`

多格式文档内容提取，输出统一 `ParseResult`（含分页文本列表）。

| 格式 | 解析库 |
|------|--------|
| PDF | `pypdf` |
| DOCX | `python-docx` |
| XLSX | `openpyxl` |
| PPTX | `python-pptx` |
| TXT / MD | 原生读取 |
| HTML | `BeautifulSoup4` |

### `apps/chunking/`

文本分块，由 **LlamaIndex** 全权实现，支持两种策略：

| 策略名 | 实现 | 说明 |
|--------|------|------|
| `sentence`（默认） | `SentenceSplitter` | 按句子边界分割，`chunk_size` 单位为 token，确定性、零外部依赖 |
| `semantic` | `SemanticSplitterNodeParser` | 基于 embedding 相似度检测语义边界，需要 `OPENAI_API_KEY` |

`BaseChunker` 提供 `split_text(text, page)` 和 `split_pages(pages)` 接口，`get_chunker(strategy, chunk_size, chunk_overlap)` 工厂方法统一实例化。

### `apps/embeddings/`

OpenAI 嵌入服务封装：

- `constants.py`：`MODEL_DIMENSIONS` 字典，维护模型名称 → 向量维度映射（`text-embedding-3-small`: 1536, `text-embedding-3-large`: 3072, `text-embedding-ada-002`: 1536），由 views 和 tasks 共享导入
- 批量调用，自动处理速率限制
- 支持按知识库配置使用不同嵌入模型

### `apps/vector_store/`

Qdrant 向量库封装。

| 文件 | 说明 |
|------|------|
| `service.py` | `VectorStoreService`：`upsert_chunks(points, collection_name=None)`、`query_points()`（qdrant-client 1.17 API）、`delete_by_document(doc_id, collection_name=None)`、`ensure_collection(collection_name=None, vector_size=None)` |
| `management/commands/init_qdrant.py` | Django 管理命令，创建共享 collection 并建立 payload 索引（`tenant_id`、`knowledge_base_id`、`document_id`、`source_type`） |

**Collection 路由**：
- 默认共享 collection：`document_chunks`（`QDRANT_COLLECTION` 配置）
- 重建后每个 KB 拥有独立 collection：`{QDRANT_COLLECTION}_kb_{kb_id_hex}`
- 所有写入/读取均读取 `kb.collection_name or vs.collection`，路由正确目标

每个向量 payload 包含：`tenant_id`、`knowledge_base_id`、`document_id`、`chunk_id`、`source_type`、`source_name`、`chunk_index`、`page`、`url`、`embedding_model`

### `apps/retrieval/`

RAG 核心三件套。

| 文件 | 说明 |
|------|------|
| `service.py` | `RetrievalService.search()`：调用 embeddings → Qdrant 检索 → 记录审计日志；返回 `SearchResult`（含 chunks、latency_ms、total） |
| `prompt_builder.py` | `PromptBuilder.build()`：将检索结果拼装为 LLM 上下文，估算 Token 数 |
| `answer_service.py` | `AnswerService.answer()`：调用 retrieval → prompt_builder → OpenAI/Anthropic → 记录 RAG 日志；支持按 `llm_model` 参数切换 |
| `views.py` | 三个 API：`search_view`、`prompt_view`、`answer_view` |

**LLM 路由逻辑**：
- `model` 含 `claude` → 使用 Anthropic SDK
- 其余 → 使用 OpenAI SDK

### `apps/audit/`

自动审计日志，不需要业务层手动调用。

| 模型 | 记录内容 |
|------|----------|
| `RetrievalLog` | query、knowledge_base_id、top_k、result_count、latency_ms、caller |
| `QueryLog` | query、answer（摘要）、llm_model、prompt_tokens、completion_tokens、latency_ms |

---

## 5. 前端模块详解

### `store/`

| 文件 | 说明 |
|------|------|
| `store/index.ts` | 创建 Redux Store，集成 RTK Query 中间件 |
| `store/hooks.ts` | `useAppDispatch`、`useAppSelector`（类型安全封装） |
| `store/slices/authSlice.ts` | 登录态：`user`、`access`（JWT）、`refresh`，持久化到 `localStorage` |
| `store/api/baseApi.ts` | RTK Query base：自动在 Header 注入 `Authorization: Bearer {token}`，Tag 类型声明 |

### `store/api/` — RTK Query 端点

| 文件 | 端点 | 说明 |
|------|------|------|
| `knowledgeBaseApi.ts` | list / get / create / update / delete / rebuild | 知识库 CRUD + 重建触发，`KnowledgeBase` 类型含 `rebuild_status`、`rebuild_progress`、`collection_name` |
| `documentApi.ts` | list / upload / importUrl / delete / reindex / chunks | 文档操作，`upload` 使用 `FormData` |
| `faqApi.ts` | list / get / create / update / delete / bulkImport | FAQ CRUD |
| `retrievalApi.ts` | search / getAnswer | 两个 Mutation，返回检索结果和 RAG 答案 |

RTK Query 自动处理：缓存、Loading 状态、Tag 失效（`invalidatesTags`）。

### `pages/`

| 页面 | 路由 | 主要功能 |
|------|------|----------|
| `LoginPage` | `/login` | Email + Password 登录，暗色玻璃态设计 |
| `DashboardPage` | `/dashboard` | 统计卡片（知识库数、文档数、分块数）、最近 KB 表格、快捷入口 |
| `KnowledgeBasesPage` | `/knowledge-bases` | 知识库列表、新建/编辑（chunk_size、chunk_overlap、top_k 配置）、每行 Reindex 按钮（切换嵌入模型 + 异步重建）、进度条展示、完成/失败通知 |
| `DocumentsPage` | `/knowledge-bases/:kbId/documents` | 文件上传、URL 导入、状态追踪、分块预览 Drawer |
| `FAQPage` | `/knowledge-bases/:kbId/faq` | FAQ 列表、嵌入状态、新建/编辑 Modal |
| `RetrievalTestPage` | `/retrieval` | 向量检索 / RAG 问答双模式测试，结果可视化 |
| `JobsPage` | `/jobs` | 按 KB 筛选文档处理状态、进度条、错误信息 |
| `LogsPage` | `/logs` | 检索日志 + 问答日志分 Tab，延迟着色 |

### `components/Layout/MainLayout.tsx`

应用骨架：

- 左侧固定侧边栏（可折叠），渐变 active 状态，图标导航
- 顶部粘性 Header（玻璃态模糊背景），用户下拉菜单（显示邮箱、退出）
- `<Outlet />` 渲染当前路由页面

---

## 6. 数据流与前后端交互

### 认证流程

```
用户输入 email + password
    ↓
POST /api/v1/auth/login/
    ↓ 返回 { access, refresh, user: {id, email, username, tenant_id, role} }
Redux authSlice.setCredentials() → 存入 localStorage
    ↓
后续所有请求 Header 自动携带：
    Authorization: Bearer {access_token}
```

### API 代理（开发环境）

前端运行在 `:5173`，后端运行在 `:8000`。Vite 配置代理：

```
前端请求 /api/v1/xxx
    → Vite 代理转发 → http://localhost:8000/api/v1/xxx
    → Django 处理 → 返回 JSON
```

生产环境使用 Nginx 反向代理，不依赖 Vite dev server。

### 文件上传流程

```
用户选择文件（前端 Upload 组件）
    ↓
POST /api/v1/knowledge-bases/{kbId}/documents/upload/   (multipart/form-data)
    ↓ Django：创建 Document 记录（status=pending）
    ↓ MinIO：存储 raw/{tenant_id}/{doc_id}/file.ext
    ↓ Celery：ingest_document.delay(doc_id)
    ← 201 { id, name, status: "pending", ... }

前端轮询或手动刷新文档列表，观察 status 变化：
pending → parsing → parsed → chunking → chunked → embedding → indexed
```

### RTK Query 缓存失效

```typescript
// 创建/删除 FAQ 后自动 refetch 列表
invalidatesTags: ["FAQ"]

// 上传文档后自动 refetch 文档列表
invalidatesTags: ["Document"]
```

---

## 7. 核心 RAG 流程

### 文档摄取流水线

```
上传文件 (POST /documents/upload/)
         │
    [Celery Worker]
         │
    ① Parse (apps.parsers)
         │  pypdf / python-docx / openpyxl / ...
         │  → 提取文本，按页分割
         │
    ② Chunk (apps.chunking)
         │  LlamaIndex SentenceSplitter（默认）或 SemanticSplitterNodeParser
         │  chunk_size=512 tokens, overlap=64 tokens（按 KB 配置）
         │  → 生成 DocumentChunk 记录
         │
    ③ Embed (apps.embeddings)
         │  OpenAI embedding（模型由 KB 配置，默认 text-embedding-3-small 1536 dim）
         │  → 生成向量
         │
    ④ Index (apps.vector_store)
              Qdrant upsert → kb.collection_name（per-KB collection）or 共享 collection
              payload: { tenant_id, knowledge_base_id, document_id, embedding_model, ... }
              → Document.status = "indexed"
```

### RAG 问答流程

```
用户提问 (POST /api/v1/rag/answer/)
         │
    ① 嵌入问题
         │  OpenAI text-embedding-3-small → 1536 维向量
         │
    ② 向量检索 (Qdrant query_points)
         │  Filter: { tenant_id=X, knowledge_base_id=Y }
         │  Top-K 最相似分块（余弦相似度）
         │
    ③ 构建 Prompt (apps.retrieval.prompt_builder)
         │  系统提示 + 检索上下文 + 用户问题
         │  Token 估算（tiktoken）
         │
    ④ LLM 推理
         │  Claude Sonnet (Anthropic) 或 GPT-4o (OpenAI)
         │  流式或同步输出
         │
    ⑤ 记录日志 (apps.audit)
         │  QueryLog: query, answer, model, tokens, latency_ms
         │
    返回 { answer, sources, usage, latency_ms }
```

---

## 8. API 接口总览

所有接口前缀：`/api/v1/`

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login/` | 登录，返回 access + refresh token |
| POST | `/auth/token/refresh/` | 刷新 access token |
| POST | `/auth/register/` | 注册新用户 |
| GET | `/auth/me/` | 当前用户信息 |

### 租户设置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tenants/settings/` | 获取租户全局配置（embedding_model、llm_model） |
| PATCH | `/tenants/settings/` | 更新租户全局配置 |

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/knowledge-bases/` | 列表（分页） |
| POST | `/knowledge-bases/` | 创建 |
| GET/PUT/PATCH/DELETE | `/knowledge-bases/{id}/` | 详情/更新/删除 |
| POST | `/knowledge-bases/{id}/rebuild/` | 触发异步重建（切换嵌入模型），返回 KB 最新状态 |

### 文档

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/knowledge-bases/{kbId}/documents/` | 文档列表 |
| POST | `/knowledge-bases/{kbId}/documents/upload/` | 上传文件（multipart） |
| POST | `/knowledge-bases/{kbId}/documents/import-url/` | 导入 URL |
| GET | `/knowledge-bases/{kbId}/documents/{id}/chunks/` | 文档分块列表 |
| POST | `/knowledge-bases/{kbId}/documents/{id}/reindex/` | 重新索引 |
| DELETE | `/knowledge-bases/{kbId}/documents/{id}/` | 删除文档 |

### FAQ

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/knowledge-bases/{kbId}/faq/` | FAQ 列表（支持搜索） |
| POST | `/knowledge-bases/{kbId}/faq/` | 创建 FAQ |
| PUT/PATCH | `/knowledge-bases/{kbId}/faq/{id}/` | 更新 FAQ |
| DELETE | `/knowledge-bases/{kbId}/faq/{id}/` | 删除 FAQ |
| POST | `/knowledge-bases/{kbId}/faq/bulk-import/` | 批量导入 `{items: [{question, answer}]}` |

### 检索与 RAG

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/retrieval/search/` | 向量检索，返回相关分块 |
| POST | `/rag/prompt/` | 构建 RAG Prompt（不调用 LLM） |
| POST | `/rag/answer/` | 完整 RAG 问答（检索 + LLM） |

**`/retrieval/search/` 请求体：**
```json
{
  "query": "什么是 RAG？",
  "knowledge_base_id": "uuid",
  "top_k": 5,
  "score_threshold": 0.0,
  "filters": {}
}
```

**`/rag/answer/` 请求体：**
```json
{
  "query": "什么是 RAG？",
  "knowledge_base_id": "uuid",
  "top_k": 5,
  "llm_model": "claude-sonnet-4-6"
}
```

### 任务 & 审计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/jobs/parse/{docId}/` | 解析任务详情 |
| GET | `/jobs/embed/{docId}/` | 嵌入任务详情 |
| GET | `/audit/retrieval/` | 检索审计日志 |
| GET | `/audit/queries/` | RAG 问答审计日志 |

### Swagger 文档

访问 `http://localhost:8000/api/schema/swagger-ui/` 查看完整交互式 API 文档。

---

## 9. 配置说明

### 后端 `backend/.env`

```ini
# ─── Django ────────────────────────────────────────────────
DJANGO_SETTINGS_MODULE=config.settings.development
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# ─── PostgreSQL ────────────────────────────────────────────
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=demo           # 数据库名
DB_USER=your_db_user
DB_PASSWORD=your_db_pass
DB_SCHEMA=rag              # PostgreSQL schema（命名空间）

# ─── MinIO（S3 兼容对象存储）──────────────────────────────
MINIO_URL=localhost:19000
MINIO_USER=admin
MINIO_PASSWORD=admin123
MINIO_BUCKET=rag-documents
MINIO_SECURE=False         # True 时使用 HTTPS

# ─── Qdrant（向量数据库）──────────────────────────────────
VDB_HOST=localhost
VDB_PORT=6333
QDRANT_COLLECTION=document_chunks
QDRANT_API_KEY=            # 可留空（本地无认证）

# ─── Redis / Celery ────────────────────────────────────────
REDIS_URL=redis://:password@localhost:6379/0

# ─── LLM / 嵌入模型 ───────────────────────────────────────
OPENAI_KEY=sk-proj-...         # OpenAI API Key（嵌入 + GPT）
ANTHROPIC_API_KEY=sk-ant-...   # Anthropic API Key（Claude）
DEFAULT_LLM_MODEL=claude-sonnet-4-6
DEFAULT_EMBEDDING_MODEL=text-embedding-3-small
DEFAULT_EMBEDDING_DIM=1536

# ─── CORS ──────────────────────────────────────────────────
CORS_ALLOW_ALL=True
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# ─── 上传限制 ──────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB=100
```

### 前端 `frontend/.env`

```ini
VITE_API_URL=http://localhost:8000   # 后端地址（Vite 代理目标）
VITE_APP_NAME=RAG Platform           # 应用名称（显示在侧边栏和登录页）
```

### 配置读取方式

- **后端**：`python-decouple` 的 `config()` 函数，自动从 `.env` 文件或环境变量读取
- **前端**：Vite 内置 `import.meta.env.VITE_*` 变量，编译时注入

---

## 10. 环境搭建与启动

### 前提条件

确保以下服务已运行：

```bash
# PostgreSQL（创建数据库和 schema）
psql -U postgres -c "CREATE DATABASE demo;"
psql -d demo -c "CREATE SCHEMA IF NOT EXISTS rag;"

# Redis（带密码）
redis-server --requirepass 123456

# Qdrant（本地 Docker）
docker run -d -p 6333:6333 qdrant/qdrant

# MinIO（本地 Docker）
docker run -d -p 19000:9000 -p 19001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=admin123 \
  minio/minio server /data --console-address ":9001"
```

### 后端启动

```bash
cd backend

# 1. 安装依赖（uv 自动创建虚拟环境）
uv sync

# 2. 复制并编辑配置
cp .env.example .env   # 填入实际值

# 3. 数据库迁移
uv run python src/manage.py migrate

# 4. 初始化 Qdrant collection
uv run python src/manage.py init_qdrant

# 5. 创建管理员用户（可选）
uv run python src/manage.py createsuperuser

# 6. 启动 Django 开发服务器
uv run python src/manage.py runserver

# 7. 启动 Celery Worker（新终端窗口）
cd src
uv run celery -A config.celery worker --loglevel=info
```

后端服务地址：`http://localhost:8000`
Admin 控制台：`http://localhost:8000/admin/`
Swagger 文档：`http://localhost:8000/api/schema/swagger-ui/`

### 前端启动

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 复制并编辑配置
cp .env.example .env

# 3. 启动开发服务器
npm run dev
```

前端访问地址：`http://localhost:5173`

> 开发环境下，所有 `/api/*` 请求通过 Vite 代理自动转发到后端，无需手动配置跨域。

### 生产构建

```bash
# 前端
cd frontend && npm run build
# 产物在 frontend/dist/，由 Nginx 托管

# 后端
uv run python src/manage.py collectstatic
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## 11. 运行测试

### 测试架构

```
src/tests/
├── conftest.py          # 全局 Fixtures
├── test_auth.py         # 认证接口（登录、Token、注册）
├── test_knowledge_bases.py  # 知识库 CRUD
├── test_documents.py    # 文档上传、URL 导入、分块（Mock MinIO + Celery）
├── test_faq.py          # FAQ CRUD、批量导入（Mock Celery）
└── test_retrieval.py    # 检索搜索、RAG 问答（Mock vector_store + LLM）
```

**Fixtures 说明（conftest.py）**：

| Fixture | 作用 |
|---------|------|
| `django_db_setup` | Session 级别，确保 `rag` schema 存在 |
| `api_client` | DRF APIClient 实例 |
| `tenant` | 创建测试租户 |
| `user` | 创建关联该租户的测试用户 |
| `auth_client` | 已认证的 APIClient（`force_authenticate`） |
| `knowledge_base` | 创建测试知识库 |

### 运行测试

```bash
cd backend

# 运行全部测试
uv run pytest

# 复用数据库（加速，跳过 migrate）
uv run pytest --reuse-db

# 指定测试文件
uv run pytest src/tests/test_faq.py

# 指定测试类或方法
uv run pytest src/tests/test_documents.py::TestDocumentUpload::test_upload_success

# 显示详细输出
uv run pytest -v

# 显示标准输出（print）
uv run pytest -s

# 查看覆盖率
uv run pytest --cov=apps --cov-report=html
```

### 测试策略

- **MinIO**：所有涉及文件操作的测试用 `mocker.patch("apps.documents.views.minio_client", MagicMock())` Mock，不连接真实 MinIO
- **后台任务**：涉及异步任务的测试 Mock `run_async` 或相关服务函数，任务只触发不执行
- **LLM / Qdrant**：检索测试中通过 `container.retrieval_service.override(mock_svc)` 覆盖 DI 容器，不连接真实服务
- **数据库**：使用真实 PostgreSQL 的 `test_demo` 库（需要 `rag` schema 预先存在）

### 当前测试覆盖

```
27 passed ✓

test_auth.py          — 登录成功/失败、Token 刷新、受保护接口
test_knowledge_bases.py — CRUD、权限隔离
test_documents.py     — 上传（无文件/成功）、URL 导入、分块预览
test_faq.py           — 创建/列表/删除/批量导入
test_retrieval.py     — 向量搜索、RAG 问答、错误处理
```

---

## 12. Docker 部署

项目提供 `Dockerfile`，支持容器化部署（不包含 Compose 编排，基础设施服务需单独启动）。

### 后端 Dockerfile

位置：`backend/Dockerfile`

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 复制依赖文件
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 复制源码
COPY src/ ./src/

ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=config.settings.production

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
```

### 前端 Dockerfile

位置：`frontend/Dockerfile`

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 构建镜像

```bash
# 后端
docker build -t rag-backend ./backend

# 前端
docker build -t rag-frontend ./frontend

# 运行后端（需外部基础设施）
docker run -d \
  --env-file backend/.env \
  -p 8000:8000 \
  rag-backend

# 运行前端
docker run -d -p 80:80 rag-frontend
```

### 环境变量（容器）

容器运行时通过 `--env-file` 或 `-e` 传入 `.env` 中的所有变量。生产环境将 `DB_HOST`、`MINIO_URL`、`VDB_HOST`、`REDIS_URL` 改为实际服务地址。

---

## 附录：常见问题

### Q: Qdrant 连接失败（SSL Error）

Qdrant 默认不需要 API Key。如果 `QDRANT_API_KEY` 为空，客户端初始化时**不要**传入 `api_key` 参数，否则会强制启用 HTTPS 导致连接失败。已修复：代码只在 `QDRANT_API_KEY` 非空时才传入。

### Q: Celery 任务不执行

检查：
1. Redis 服务是否运行，密码是否正确（`REDIS_URL` 中包含 `:password@`）
2. Celery Worker 是否已启动（`celery -A config.celery worker`）
3. Worker 启动目录是否为 `backend/src/`

### Q: pytest 报 `rag` schema 不存在

在测试数据库中手动创建：
```sql
\c test_demo
CREATE SCHEMA IF NOT EXISTS rag;
```

或者确保 PostgreSQL 用户有 CREATEDB 权限（`ALTER USER xxx CREATEDB;`）后重新运行，conftest 中的 `django_db_setup` fixture 会自动创建 schema。

### Q: `OPENAI_KEY` vs `OPENAI_API_KEY`

`settings/base.py` 同时支持两种命名，优先读取 `OPENAI_KEY`，回退到 `OPENAI_API_KEY`：
```python
OPENAI_API_KEY = config("OPENAI_KEY", default=config("OPENAI_API_KEY", default=""))
```

### Q: 前端 API 请求返回 401

JWT access token 有效期 1 小时，过期后需刷新。前端 `authSlice` 将 token 存入 `localStorage`，刷新页面后自动恢复。如持续 401，清除 localStorage 重新登录。
