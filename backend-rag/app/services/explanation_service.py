import re
from typing import Any

from app.core.config import get_settings
from app.langchain_app.chains import LLMNotConfiguredError, generate_diagnosis_text
from app.langchain_app.rag import retrieve_knowledge_hits, format_knowledge_hits


LLM_DISABLED_MESSAGE = "当前未启用大语言模型，请在 .env 中配置 ENABLE_LLM=true 和模型 API 参数。"


def build_fallback_explanation(model_result: dict[str, Any]) -> tuple[str, list[str]]:
    fault_name = model_result.get("dominant_fault_name", "未知故障")
    label = model_result.get("dominant_label", "未知")
    ratio = model_result.get("dominant_ratio")
    confidence = model_result.get("avg_confidence")

    reminder = ""
    if "请修改" in str(fault_name):
        reminder = " 当前标签映射仍是占位名称，请先完善 saved_models/label_map.json。"

    explanation = (
        f"模型多数投票结果为标签 {label}（{fault_name}），"
        f"主导比例为 {ratio}，平均置信度为 {confidence}。"
        f"{reminder}由于 ENABLE_LLM=false，本次未调用大语言模型生成扩展解释。"
    )
    suggestions = [
        "结合关键运行参数和现场工况复核该诊断结论。",
        "优先检查与主导故障相关的传感器、阀门、水泵、换热器和压力温度指标。",
        "维修或调整后重新采集同一工况数据并复诊，比较预测分布是否收敛。",
    ]
    return explanation, suggestions


def extract_maintenance_suggestions(text: str) -> list[str]:
    suggestions: list[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "维修建议" in stripped:
            in_section = True
            continue
        if in_section and re.match(r"^\d+[.、]|^-", stripped):
            suggestions.append(re.sub(r"^\d+[.、]\s*|^-\s*", "", stripped))
        elif in_section and re.match(r"^\d+\.", stripped):
            suggestions.append(stripped)
        elif in_section and any(key in stripped for key in ["后续监测", "诊断结论"]):
            break
    return suggestions[:10]


def extract_section_items(text: str, section_name: str, max_items: int = 10) -> list[str]:
    items: list[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        heading = stripped.lstrip("#").strip()
        if section_name in heading:
            in_section = True
            continue
        if in_section and re.match(r"^#{1,6}\s+", stripped):
            break
        if in_section and re.match(r"^\d+[.、]\s+|^[-*]\s+", stripped):
            items.append(re.sub(r"^\d+[.、]\s+|^[-*]\s+", "", stripped))
        elif in_section and any(key in stripped for key in ["诊断结论", "主要依据", "可能原因", "后续监测建议"]):
            break
    return items[:max_items]


def generate_explanation(
    model_result: dict[str, Any],
    dataset_summary: dict[str, Any],
) -> tuple[str, list[str]]:
    settings = get_settings()
    if not settings.enable_llm:
        return build_fallback_explanation(model_result)

    query = f"{model_result.get('dominant_label')} {model_result.get('dominant_fault_name')}"
    context = ""
    if settings.enable_rag:
        context = format_knowledge_hits(retrieve_knowledge_hits(query))
    try:
        text = generate_diagnosis_text(model_result, dataset_summary, context)
    except LLMNotConfiguredError as exc:
        return str(exc), []

    suggestions = extract_section_items(text, "维修建议") or extract_maintenance_suggestions(text)
    return text, suggestions
