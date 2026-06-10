import json
from typing import Any

from app.core.config import get_settings
from app.langchain_app.prompts import (
    CHAT_USER_TEMPLATE,
    DIAGNOSIS_SYSTEM_PROMPT,
    DIAGNOSIS_USER_TEMPLATE,
)


class LLMNotConfiguredError(RuntimeError):
    pass


def _build_llm():
    settings = get_settings()
    if not settings.enable_llm:
        raise LLMNotConfiguredError("当前未启用大语言模型，请在 .env 中配置 ENABLE_LLM=true 和模型 API 参数。")
    if not settings.openai_api_key or not settings.openai_model:
        raise LLMNotConfiguredError("大语言模型参数不完整，请配置 OPENAI_API_KEY 和 OPENAI_MODEL。")

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise LLMNotConfiguredError("未安装 langchain-openai，请先安装 requirements.txt。") from exc

    kwargs: dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "model": settings.openai_model,
        "temperature": settings.openai_temperature,
        "timeout": settings.openai_timeout,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def generate_diagnosis_text(
    model_result: dict[str, Any],
    dataset_summary: dict[str, Any],
    context: str,
) -> str:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
    except ImportError as exc:
        raise LLMNotConfiguredError("未安装 LangChain 依赖，请先安装 requirements.txt。") from exc

    llm = _build_llm()
    user_content = DIAGNOSIS_USER_TEMPLATE.format(
        model_result=json.dumps(model_result, ensure_ascii=False, indent=2),
        dataset_summary=json.dumps(dataset_summary, ensure_ascii=False, indent=2),
        context=context or "暂无知识库片段。",
    )
    response = llm.invoke([
        SystemMessage(content=DIAGNOSIS_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])
    return str(response.content)


def generate_chat_answer(
    diagnosis_context: dict[str, Any],
    chat_history: str,
    context: str,
    question: str,
) -> str:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
    except ImportError as exc:
        raise LLMNotConfiguredError("未安装 LangChain 依赖，请先安装 requirements.txt。") from exc

    llm = _build_llm()
    user_content = CHAT_USER_TEMPLATE.format(
        diagnosis_context=json.dumps(diagnosis_context, ensure_ascii=False, indent=2),
        chat_history=chat_history or "暂无历史对话。",
        context=context or "暂无知识库片段。",
        question=question,
    )
    response = llm.invoke([
        SystemMessage(content=DIAGNOSIS_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])
    return str(response.content)
