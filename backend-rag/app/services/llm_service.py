from app.core.config import get_settings
from app.schemas.rag import ChatTurn


class LLMNotConfiguredError(RuntimeError):
    pass


SYSTEM_PROMPT = """你是冷水机组故障诊断知识库问答助手。
你必须基于给定知识库片段回答，不要编造知识库中不存在的事实。
如果知识库片段不足以回答，请明确说明不确定，并建议补充运行数据或现场检查结果。
回答应专业、可执行，维修建议优先给出现场检查步骤。
"""


USER_TEMPLATE = """知识库片段：
{context}

历史对话：
{chat_history}

用户问题：
{question}

请用中文回答，并在最后列出你参考的来源文件名。
"""


def _build_chat_model():
    settings = get_settings()
    if not settings.llm_configured:
        raise LLMNotConfiguredError("大语言模型未启用或参数不完整，请配置 ENABLE_LLM=true、OPENAI_API_KEY 和 OPENAI_MODEL。")

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise LLMNotConfiguredError("未安装 langchain-openai，请先安装 requirements.txt。") from exc

    kwargs = {
        "api_key": settings.openai_api_key,
        "model": settings.openai_model,
        "temperature": settings.openai_temperature,
        "timeout": settings.openai_timeout,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def generate_rag_answer(question: str, context: str, chat_history: list[ChatTurn]) -> str:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
    except ImportError as exc:
        raise LLMNotConfiguredError("未安装 LangChain 依赖，请先安装 requirements.txt。") from exc

    history_text = "\n".join(f"{turn.role}: {turn.content}" for turn in chat_history[-10:]) or "暂无历史对话。"
    user_content = USER_TEMPLATE.format(
        context=context or "暂无知识库片段。",
        chat_history=history_text,
        question=question,
    )
    response = _build_chat_model().invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
    )
    return str(response.content)

