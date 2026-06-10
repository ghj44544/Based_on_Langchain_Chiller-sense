# 冷水机组故障诊断智能系统前端

Vue 3 + Vite + TypeScript + Element Plus 的前端 MVP，默认对接已有 FastAPI 后端：

```env
VITE_API_BASE_URL=http://127.0.0.1:8010
```

## 运行

```bash
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:5173
```

## 构建

```bash
npm run build
```

## 功能

- 首页工作台显示后端健康状态和 MATLAB / LLM / RAG 状态
- 上传 Excel / CSV 调用 `/api/diagnosis/upload`
- 诊断结果卡片、数据集摘要和 ECharts 预测分布图
- Markdown 报告生成
- 诊断问答，后端未启用 LLM 时按业务提示展示

前端不包含登录注册，不重新实现后端逻辑，不 mock 后端数据。
