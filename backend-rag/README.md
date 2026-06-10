# Chiller Sense Backend RAG

这是 `backend/` 的增强版后端，保留原有冷水机组故障诊断能力，并扩展完整 LangChain + RAG 检索问答能力。

它与原 `backend/` 分开，便于对比和回滚；但功能目标不是重做，而是在原接口基础上增强 RAG。
默认 SQLite 数据库为 `chiller_fault_rag.db`，避免和原 `backend/chiller_fault.db` 混用。

## 功能

- 上传 RP1043 格式 Excel / CSV
- 按 `saved_models/feature_columns.json` 校验字段
- `label` 仅作为可选摘要字段，不参与模型输入
- 调用 `saved_models/fault_model.pkl` 进行批量预测
- 可选加载 `saved_models/scaler.pkl`
- 保存诊断历史和问答历史到 SQLite
- `ENABLE_LLM=false` 时仍可启动并完成模型诊断
- `ENABLE_LLM=true` 时通过 LangChain 生成解释、维修建议和多轮问答
- 生成 Markdown 诊断报告

## 运行

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 配置

复制环境变量模板：

```bash
copy .env.example .env
```

默认 `ENABLE_LLM=false`，系统不会调用大语言模型。要启用解释和问答，请配置：

```env
ENABLE_LLM=true
ENABLE_RAG=true
OPENAI_API_KEY=你的Key
OPENAI_BASE_URL=https://你的OpenAI兼容地址/v1
OPENAI_MODEL=你的模型名
OPENAI_TEMPERATURE=0.2
OPENAI_TIMEOUT=60
```

启用后：

- 上传诊断时会调用 LangChain 生成“诊断结论、主要依据、可能原因、维修建议、后续监测建议”。
- `POST /api/chat` 可以围绕某次诊断记录继续问答。
- `ENABLE_RAG=true` 时会检索 `knowledge_base/*.md`，并把命中的知识库片段注入提示词。
- 增强 RAG 支持 `keyword`、`vector`、`hybrid` 三种检索模式。
- 未配置 Embedding 时，`vector` / `hybrid` 会自动降级到关键词检索，保证原接口可用。

聊天示例：

```json
{
  "diagnosis_id": 1,
  "question": "为什么判断为这个故障？应该优先检查哪里？"
}
```

返回中会包含：

```json
{
  "answer": "...",
  "sources": ["fault_types.md", "reduced_condenser_water_flow.md"]
}
```

可以通过健康检查确认 LLM 状态：

```text
GET /api/health
```

关注字段：

```json
{
  "llm_enabled": true,
  "llm_configured": true,
  "rag_enabled": true,
  "rag_retriever": "hybrid",
  "embedding_configured": true,
  "knowledge_chunks": 11
}
```

## 增强 RAG 接口

除原有 `POST /api/chat` 外，`backend-rag` 额外提供独立知识库接口：

```text
GET  /api/rag/sources
POST /api/rag/search
POST /api/rag/ask
POST /api/rag/reindex
```

检索示例：

```json
{
  "query": "制冷剂泄漏应该优先检查哪里？",
  "retriever": "hybrid",
  "top_k": 4
}
```

问答示例：

```json
{
  "question": "制冷剂泄漏有哪些维修建议？",
  "retriever": "hybrid",
  "top_k": 4
}
```

## 模型文件

当前默认使用 MATLAB ultra 最终模型：

```text
M1DCNN-集成/saved_models_ultra/largeDataset_enhanced_model.mat
```

并通过 MATLAB Engine 调用：

```text
app/matlab/chiller_ultra_predict.m
```

如果改用 Python / scikit-learn 模型，请将训练好的模型放到：

```text
saved_models/fault_model.pkl
```

如果训练时使用了 scaler，请放到：

```text
saved_models/scaler.pkl
```

使用 `.mat` 模型时不使用 `scaler.pkl`，保持 MATLAB 训练脚本中的预处理逻辑。运行前需要确保当前虚拟环境能导入 MATLAB Engine：

```bash
python -c "import matlab.engine; print('matlab engine ok')"
```

如果未安装，请在 MATLAB 安装目录下执行对应的 engine 安装命令。

注意：当前 `largeDataset_enhanced_model.mat` 的 `config.cnn.numFeatures` 是 12。RP1043 原始数据仍按 64 个字段校验，但模型预测前需要用训练该模型时的 12 个特征列构造输入。请创建：

```text
saved_models/model_feature_columns.json
```

内容示例：

```json
[
  "请替换为训练时第1个特征名",
  "请替换为训练时第2个特征名"
]
```

然后在 `.env` 中设置：

```env
MODEL_FEATURE_COLUMNS_PATH=saved_models/model_feature_columns.json
```

如果 Python 可以 `import matlab.engine`，但 `start_matlab()` 失败，可以改用共享 MATLAB 会话：

1. 先手动打开 MATLAB。
2. 在 MATLAB 命令窗口执行：

```matlab
matlab.engine.shareEngine
```

3. 后端 `.env` 中设置：

```env
MATLAB_ENGINE_MODE=connect
```

4. 重启 FastAPI 服务。

`saved_models/feature_columns.json` 是后端读取特征的唯一依据。不要手动从代码中删除 `Unit Status` 和 `Active Fault`，是否参与模型输入由该 JSON 决定。

请根据真实训练逻辑修改：

```text
saved_models/label_map.json
```

## API

- `POST /api/diagnosis/upload`
- `POST /api/chat`
- `POST /api/report/generate/{diagnosis_id}`
- `GET /api/report/latest/{diagnosis_id}`
- `GET /api/report/download/{report_filename}`
- `GET /api/report/download/latest/{diagnosis_id}`
- `GET /api/meta/features`
- `GET /api/meta/labels`
- `GET /api/health`

所有接口使用统一返回格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

报告生成接口返回示例：

```json
{
  "report_path": "E:\\个人项目\\chiller-sense\\backend\\reports\\diagnosis_report_1_20260610020929.md",
  "report_filename": "diagnosis_report_1_20260610020929.md",
  "download_url": "/api/report/download/diagnosis_report_1_20260610020929.md"
}
```

支持的报告格式：

```text
md
html
docx
```

生成指定格式：

```text
POST /api/report/generate/1?report_format=html
POST /api/report/generate/1?report_format=docx
```

前端下载时可以直接访问：

```text
GET http://127.0.0.1:8000/api/report/download/diagnosis_report_1_20260610020929.md
```

如果只知道诊断记录 ID，可以访问：

```text
GET http://127.0.0.1:8000/api/report/download/latest/1
GET http://127.0.0.1:8000/api/report/download/latest/1?report_format=html
GET http://127.0.0.1:8000/api/report/download/latest/1?report_format=docx
```

DOCX 导出需要安装：

```bash
pip install python-docx
```

如果未安装，接口会返回清晰错误提示。HTML 和 Markdown 不需要额外依赖。

## 测试

```bash
pytest
```
