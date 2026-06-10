import json
from typing import Any

from app.langchain_app.rag import retrieve_knowledge


def chiller_fault_diagnosis_tool(diagnosis_result: dict[str, Any] | str) -> str:
    """Return a compact expert explanation input for LangChain agent/tool use."""
    if isinstance(diagnosis_result, str):
        payload = json.loads(diagnosis_result)
    else:
        payload = diagnosis_result

    model_result = payload.get("model_result", payload)
    fault_name = model_result.get("dominant_fault_name", "未知故障")
    context = retrieve_knowledge(str(fault_name))
    return (
        f"诊断类别: {model_result.get('dominant_label')}\n"
        f"故障名称: {fault_name}\n"
        f"主导比例: {model_result.get('dominant_ratio')}\n"
        f"平均置信度: {model_result.get('avg_confidence')}\n"
        f"预测分布: {model_result.get('prediction_distribution')}\n\n"
        f"知识库参考:\n{context}"
    )

