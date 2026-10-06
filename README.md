# 囤囤 TUNTUN

自托管的个人知识 / 效率系统。核心抽象：**一切皆是卡片**——单词、面试题、考点、书摘共用同一套 FSRS 复习引擎，且每张卡片都能溯源回原文位置。

> 本仓库是正式工程（前后端分离）。设计参考 `../demo/index.html`（单文件零依赖原型），视觉系统与视图结构一一对应。完整需求与技术方案见 `../知栈-需求与技术文档.html`。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12+ · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL 16 + pgvector · py-fsrs · LiteLLM |
| 前端 | Vue 3.5 · TypeScript · Vite · Pinia · Vue Router · Element Plus · ECharts · UnoCSS |
| 部署 | Docker Compose |

## 目录结构

```
zhistack/
├── backend/            # FastAPI 后端
│   └── app/
│       ├── core/       # 配置 / 安全 / 依赖注入 / 异常
│       ├── db/         # 引擎、会话、初始化
│       ├── models/     # SQLAlchemy 模型
│       ├── schemas/    # Pydantic 模型
│       ├── api/v1/     # 路由
│       └── services/   # srs / llm / rag / extract
├── frontend/           # Vue 3 前端
│   └── src/
│       ├── api/        # 请求封装（axios）
│       ├── stores/     # Pinia
│       ├── router/     # 路由与守卫
│       ├── layouts/    # MainLayout / BlankLayout
│       ├── views/      # 页面
│       ├── components/ # 组件
│       └── styles/     # 设计 token（三主题贴纸卡通）
└── docker-compose.yml
```

## 本地开发

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env          # 按需修改 SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

开发态默认 SQLite（`sqlite+aiosqlite:///./data/zhistack.db`），无需装数据库。切 PostgreSQL 只需改 `DB_DSN`。

### 前端

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173，/api 代理到 8000
```

### 一键起（生产）

```bash
cp .env.example .env && 改 SECRET_KEY 与 DB_PASSWORD
docker compose up -d --build
# 前端 http://localhost:8080
```

## 里程碑（当前进度）

- [x] **M1 骨架**：项目初始化、认证（注册/登录/JWT/刷新）、前后端联调
- [x] **M2 复习核心**：卡组卡片 CRUD、FSRS 引擎、复习界面
- [x] **M3 内容库**：文件上传、目录树、解析管道（TXT/MD/PDF）
- [x] **M4 AI 生成**：LLM 抽象层、划词成卡
- [ ] **M5 问答**：Embedding、向量检索、RAG（`services/rag` 空包，尚未开始）
- [x] **M6 AI 提炼**：文件 → Markdown 笔记 → 拆卡
- [x] **M7 效率**：番茄钟、专注记录、统计看板
- [ ] **M8 集成与打磨**

## 环境变量

完整清单见 `.env.example`。关键项：`SECRET_KEY`（必须改）、`DB_DSN`（数据库连接串）、`LLM_PROVIDERS__*__API_KEY`（M4 起需要）。
