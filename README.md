# Based on LangChain Chiller Sense

基于 FastAPI、LangChain、Vue 3 和 MATLAB Engine 的冷水机组故障诊断系统。项目采用前后端分离结构，后端负责数据上传、特征校验、模型预测、诊断解释、报告生成和问答接口，前端负责诊断工作台、文件上传、结果展示、报告下载和智能问答交互。

> 注意：仓库不包含真实环境配置、数据库、上传数据、诊断报告、MATLAB 模型文件和 `backend/M1DCNN-集成/` 目录。部署或本地运行时需要自行准备这些文件。

## 项目结构

```text
chiller-sense/
├── backend/                 # FastAPI 后端
│   ├── app/                 # API、服务、数据库、LangChain、MATLAB 调用代码
│   ├── knowledge_base/      # RAG 知识库 Markdown
│   ├── saved_models/        # 特征列、标签映射等轻量配置
│   ├── tests/               # 后端测试
│   ├── .env.example         # 后端环境变量模板
│   └── requirements.txt
├── backend-rag/             # backend 的增强版，保留原功能并扩展完整 RAG
│   ├── app/                 # 原后端 API、诊断服务、报告服务、RAG 检索和问答服务
│   ├── knowledge_base/      # RAG Markdown 知识库副本
│   ├── tests/               # RAG 后端测试
│   ├── .env.example         # RAG 环境变量模板
│   └── requirements.txt
├── frontend/                # Vue 3 前端
│   ├── src/
│   ├── .env.example         # 前端环境变量模板
│   └── package.json
├── .gitignore
└── README.md
```

## 技术栈

后端：

- Python 3.10+
- FastAPI
- SQLAlchemy + SQLite
- Pandas / NumPy / scikit-learn
- LangChain / langchain-openai / ChromaDB
- MATLAB Engine for Python
- python-docx，用于 DOCX 报告导出
- Pytest

前端：

- Vue 3
- Vite
- TypeScript
- Element Plus
- Pinia
- Vue Router
- Axios
- ECharts
- markdown-it

## 环境要求

基础环境：

- Python 3.10 或更高版本
- Node.js 18 或更高版本
- npm
- Git

如果使用当前 MATLAB ultra 模型预测，还需要：

- 已安装 MATLAB
- 已安装 MATLAB Engine for Python
- 本地存在 `backend/M1DCNN-集成/` 模型工程目录
- 本地存在最终模型文件，例如 `backend/M1DCNN-集成/saved_models_ultra/largeDataset_enhanced_model.mat`

如果只测试接口结构、报告导出或前端页面，可以先关闭 LLM，并根据实际情况跳过 MATLAB 模型预测。

## 后端启动

进入后端目录：

```powershell
cd backend
```

创建并启用虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

安装依赖：

```powershell
pip install -r requirements.txt
```

复制环境变量模板：

```powershell
copy .env.example .env
```

按本机情况修改 `.env`。最小配置示例：

```env
APP_ENV=dev
DATABASE_URL=sqlite:///./chiller_fault.db
UPLOAD_DIR=uploads
REPORT_DIR=reports

ENABLE_LLM=false
ENABLE_RAG=false
```

启动后端：

```powershell
uvicorn app.main:app --reload
```

默认接口地址：

```text
http://127.0.0.1:8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
GET /api/health
```

## MATLAB Engine 配置

确认当前 Python 环境可以导入 MATLAB Engine：

```powershell
python -c "import matlab.engine; print('matlab engine ok')"
```

如果导入失败，需要到 MATLAB 安装目录下安装 Engine。不同 MATLAB 版本路径略有不同，常见方式是在 MATLAB Engine 的 Python 目录中执行安装命令。

后端默认通过 `.env` 中这些变量定位 MATLAB 模型：

```env
MODEL_PATH=M1DCNN-集成/saved_models_ultra/largeDataset_enhanced_model.mat
MATLAB_PROJECT_DIR=M1DCNN-集成
MATLAB_PREDICT_FUNCTION_DIR=app/matlab
MATLAB_ENGINE_MODE=auto
```

如果 `start_matlab()` 启动失败，可以使用共享 MATLAB 会话：

1. 手动打开 MATLAB。
2. 在 MATLAB 命令窗口执行：

```matlab
matlab.engine.shareEngine
```

3. 在后端 `.env` 中设置：

```env
MATLAB_ENGINE_MODE=connect
```

4. 重启 FastAPI 后端。

## LLM / LangChain 配置

默认关闭大模型：

```env
ENABLE_LLM=false
ENABLE_RAG=false
```

如需启用诊断解释和智能问答，配置 OpenAI 兼容接口：

```env
ENABLE_LLM=true
ENABLE_RAG=true
LLM_PROVIDER=openai_compatible
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
OPENAI_MODEL=your_model_name
OPENAI_TEMPERATURE=0.2
OPENAI_TIMEOUT=60
```

`ENABLE_RAG=true` 时，后端会检索 `backend/knowledge_base/*.md`，并将相关知识片段注入 LangChain 提示词。

## 独立 RAG 后端

如果希望在保留现有诊断、MATLAB 调用、数据库记录、报告导出和聊天接口的基础上扩展完整 LangChain + RAG，可以使用 `backend-rag/`。该目录是 `backend/` 的增强版副本，和原 `backend/` 分开，便于对比和回滚。

启动方式：

```powershell
cd backend-rag
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8010
```

默认接口文档：

```text
http://127.0.0.1:8010/docs
```

`backend-rag` 支持原有 `/api/diagnosis`、`/api/chat`、`/api/report`、`/api/health` 等接口，并额外提供 `/api/rag/sources`、`/api/rag/search`、`/api/rag/ask`、`/api/rag/reindex`。RAG 支持关键词检索、Chroma 向量检索和 Hybrid 检索。未配置 Embedding 时会自动降级到关键词检索；配置 `OPENAI_API_KEY`、`OPENAI_MODEL` 和 `OPENAI_EMBEDDING_MODEL` 后可以启用完整向量 RAG。

## 前端启动

进入前端目录：

```powershell
cd frontend
```

安装依赖：

```powershell
npm install
```

复制前端环境变量模板：

```powershell
copy .env.example .env
```

默认后端地址：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

启动开发服务器：

```powershell
npm run dev
```

默认访问地址：

```text
http://127.0.0.1:5173
```

生产构建：

```powershell
npm run build
```

## 主要功能

- 上传 Excel / CSV 数据文件
- 基于特征列配置进行字段校验
- 调用 MATLAB ultra 模型进行故障诊断
- 展示故障类别、置信度、样本摘要和预测分布
- 生成 Markdown / HTML / DOCX 诊断报告
- 基于 LangChain 生成诊断解释和维修建议
- 支持围绕指定诊断记录进行问答
- 支持 RAG 知识库检索

## 报告导出

后端支持生成：

- Markdown
- HTML
- DOCX

接口示例：

```text
POST /api/report/generate/{diagnosis_id}?report_format=md
POST /api/report/generate/{diagnosis_id}?report_format=html
POST /api/report/generate/{diagnosis_id}?report_format=docx
```

下载最新报告：

```text
GET /api/report/download/latest/{diagnosis_id}
GET /api/report/download/latest/{diagnosis_id}?report_format=html
GET /api/report/download/latest/{diagnosis_id}?report_format=docx
```

## 测试

后端测试：

```powershell
cd backend
pytest
```

前端类型检查和构建：

```powershell
cd frontend
npm run build
```

## GitHub 上传注意事项

以下文件和目录不应提交到 GitHub：

- `.env`、`.env.local` 等真实配置文件
- 数据库文件，例如 `.db`、`.sqlite`
- 上传数据，例如 `backend/uploads/` 中的业务文件
- 生成报告，例如 `backend/reports/` 中的报告文件
- MATLAB 模型工程目录 `backend/M1DCNN-集成/`
- 模型文件，例如 `.mat`、`.pkl`、`.joblib`
- 前端依赖和缓存，例如 `node_modules/`、`dist/`、`.npm-cache/`、`.pnpm-store/`

仓库中只保留 `.env.example` 作为配置模板。真实 API Key、模型文件和实验数据请仅保存在本地或私有存储中。

## 远程仓库

GitHub 仓库地址：

```text
https://github.com/ghj44544/Based_on_Langchain_Chiller-sense.git
```
