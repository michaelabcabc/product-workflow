"""
Product Multi-Agent Workflow — Agent Definitions
每个 Agent 封装为独立函数，昂取 Context 并返回结构化输出
"""

import os
import json
from typing import Any
from openai import OpenAI
from context import WorkflowContext


# 支持通过环境变量配置，兼容任意 OpenAI Completions 兼容接口
_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-t0GO8utNzl78rZK8Vf8fsMtsQqo2LB32TsuNSPkCFsOAR6k9")
_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://aiapi.meccy.top/v1")
MODEL = os.environ.get("MODEL_NAME", "gpt-5-codex")

client = OpenAI(api_key=_API_KEY, base_url=_BASE_URL)


# ─────────────────────────────────────────────
#  辅助：调用 LLM 并返回文本
# ─────────────────────────────────────────────
def _call_llm(system: str, user: str, max_tokens: int = 4096) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content
