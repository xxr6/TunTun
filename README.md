# 囤囤 TUNTUN

囤囤是一套可自托管的知识整理与学习应用。把资料上传到内容库，在阅读时制作有原文位置的卡片，按到期时间复习；也可以用 AI 提炼笔记、安排专注时间，并在统计页查看学习记录和徽章。

## 功能概览

| 模块 | 已实现的能力 |
| --- | --- |
| 内容库与阅读器 | 上传资料、建立多级文件夹、移动文件；阅读并从原文选取内容制作卡片 |
| 卡组与复习 | 创建卡组、整理卡片、查看来源、按 FSRS 调度复习、撤销最近一次评分 |
| AI 提炼 | 从资料生成笔记和候选卡片；切换页面时保留当前提炼状态 |
| 专注 | 番茄、深度、休息、自定义倒计时和正向计时；暂停、继续、结束，按主题统计时长 |
| 今日与统计 | 今日计划、签到、到期卡提醒、专注与复习统计、徽章进度和解锁提示 |
| 个人中心 | 账户资料、主题、已获得的徽章、学习目标 |

典型使用顺序：**上传资料 → 阅读并制作卡片 → 放入卡组 → 每日复习 → 配合专注学习 → 查看统计**。AI 提炼是可选步骤；未配置模型密钥时，相关入口会使用项目内的降级逻辑或提示配置。

> 问答、任务和设置路由目前仍是占位页面。徽章的图片保存在 `frontend/src/assets/badges/`，主题、Logo 和番茄形象也属于运行时资源。

## 技术结构

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Pinia、Vue Router、Element Plus、ECharts、UnoCSS |
| 后端 | Python 3.12+、FastAPI、SQLAlchemy 2、Pydantic、FSRS |
| 数据 | 本地开发默认 SQLite；Docker Compose 配置 PostgreSQL 16 和 pgvector |
| AI | 通过 `httpx` 调用 OpenAI 兼容接口；提供商地址、模型和密钥由环境变量指定 |

`frontend/src/views/` 放页面，`frontend/src/stores/` 管理跨页面状态，`frontend/src/api/` 封装接口。后端路由在 `backend/app/api/v1/`，模型与业务逻辑分别在 `backend/app/models/`、`backend/app/services/`。API 前缀为 `/api/v1`；启动后可在 `/docs` 查看交互式接口文档。

## 本地启动

准备 Python 3.12+ 和 Node.js。后端在端口 `8000`，前端开发服务器在 `5173`，Vite 会把 `/api` 请求代理到后端。

### 后端

在 `backend` 目录执行：

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
# Windows PowerShell: Copy-Item .env.example .env
# macOS / Linux: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

开发环境默认使用 `backend/data/zhistack.db` 和 `backend/data/storage/`；目录与表会在启动时创建。首次使用请在 `backend/.env` 中设置独立的 `SECRET_KEY`。若使用 AI 功能，再配置 `LLM_BASE_URL`、`LLM_MODEL` 和 `LLM_API_KEY`。

### 前端

在另一个终端执行：

```bash
cd frontend
npm ci
npm run dev
```

打开 `http://127.0.0.1:5173`，注册账户后即可使用。检查生产构建：

```bash
cd frontend
npm run build
```

## Docker Compose

根目录的 `docker-compose.yml` 提供 PostgreSQL、后端与 Nginx 前端。先从根目录 `.env.example` 创建 `.env`，设置随机 `SECRET_KEY` 和独立的 `DB_PASSWORD`；然后执行：

```bash
docker compose up -d --build
```

默认访问地址为 `http://localhost:8080`。正式环境还需配置 HTTPS、备份和适合实际域名的 `CORS_ORIGINS`。当前项目的服务器也可采用 systemd 运行后端、Nginx 提供静态文件的部署方式；不要把服务器专用的 `.env`、数据库或上传目录提交到仓库。

## 数据与配置

- `backend/.env`：后端运行配置和密钥；根目录 `.env`：Compose 变量。两者都被 Git 忽略。
- `backend/data/`：SQLite 数据库和上传文件，必须随部署一同备份；该目录不上传 GitHub。
- 生产环境更新代码前，先做数据库在线备份，再备份上传文件。运行中的 SQLite 请使用 `sqlite3.Connection.backup()`，不要直接复制 `.db` 文件。
- 前端 `dist/`、`node_modules/`、Python 虚拟环境和测试截图属于构建或调试产物，不纳入版本库。

## 验证与现状

后端的独立流程脚本在 `backend/tests/`，可在安装后端依赖后分别运行，例如：

```bash
cd backend
python tests/test_card_quality.py
python tests/test_focus_interrupt.py
python tests/test_folder_flow.py
```

目前没有统一的数据库迁移流水线。SQLite 旧库的部分新增列由启动代码补齐；若改用 PostgreSQL 或调整数据模型，应先编写并执行正式迁移，再发布新代码。
