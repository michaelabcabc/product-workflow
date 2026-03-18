"""
Product Multi-Agent Workflow — Agent Definitions
每个 Agent 封装为独立函数，接收 Context 并返回结构化输出
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


# ═══════════════════════════════════════════════
#  Phase 1 — 需求分析
# ═══════════════════════════════════════════════

def product_manager_agent(ctx: WorkflowContext) -> dict[str, Any]:
    """PM Agent：撰写 PRD、用户故事、功能清单"""
    print("  🤖 [PM Agent] 正在分析需求并生成 PRD...")

    raw = _call_llm(
        system="""你是一位经验丰富的产品经理。根据用户的产品需求，生成一份结构化的 PRD 文档。
输出必须是合法的 JSON，包含以下字段：
{
  "product_name": "...",
  "problem_statement": "...",
  "target_users": ["用户类型1", "用户类型2"],
  "user_stories": [{"as_a": "...", "i_want": "...", "so_that": "..."}],
  "features": [{"name": "...", "priority": "Must/Should/Could/Won't", "description": "..."}],
  "success_metrics": ["指标1", "指标2"],
  "out_of_scope": ["不做的事项"]
}""",
        user=f"产品需求：{ctx.product_brief}",
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # 容错：提取 JSON 块
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"raw": raw}

    ctx.phase_outputs["requirements"]["prd"] = result
    print(f"  ✅ [PM Agent] PRD 生成完成，功能点数：{len(result.get('features', []))}")
    return result


def market_research_agent(ctx: WorkflowContext) -> dict[str, Any]:
    """Market Agent：竞品分析与市场定位"""
    print("  🤖 [Market Agent] 正在进行市场调研...")

    raw = _call_llm(
        system="""你是一位市场研究专家。根据产品描述，生成竞品分析报告。
输出必须是合法的 JSON：
{
  "competitors": [{"name": "...", "strengths": ["..."], "weaknesses": ["..."], "pricing": "..."}],
  "market_gaps": ["差异化机会1", "差异化机会2"],
  "positioning": "我们的差异化定位",
  "target_persona": {"name": "...", "age": "...", "pain_points": ["..."], "goals": ["..."]}
}""",
        user=f"产品需求：{ctx.product_brief}\n\n请分析 3-4 个主要竞品并给出市场定位建议。",
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"raw": raw}

    ctx.phase_outputs["requirements"]["market_research"] = result
    print(f"  ✅ [Market Agent] 调研完成，发现 {len(result.get('competitors', []))} 个竞品")
    return result


# ═══════════════════════════════════════════════
#  Phase 2 — UI/UX 设计
# ═══════════════════════════════════════════════

def ux_designer_agent(ctx: WorkflowContext) -> dict[str, Any]:
    """UX Agent：信息架构、用户流程、线框图规格"""
    print("  🤖 [UX Agent] 正在设计用户体验...")

    prd = ctx.phase_outputs["requirements"].get("prd", {})

    raw = _call_llm(
        system="""你是一位资深 UX 设计师。根据 PRD 设计信息架构和核心用户流程。
输出必须是合法的 JSON：
{
  "information_architecture": [{"section": "...", "pages": ["...", "..."]}],
  "user_flows": [{"name": "核心流程名", "steps": ["步骤1", "步骤2", "..."], "entry_point": "...", "exit_point": "..."}],
  "wireframes": [{"page": "...", "components": ["..."], "layout": "...", "interactions": ["..."]}],
  "ux_principles": ["设计原则1", "设计原则2"]
}""",
        user=f"PRD：{json.dumps(prd, ensure_ascii=False)}\n\n请设计完整的 UX 方案。",
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"raw": raw}

    ctx.phase_outputs["design"]["ux"] = result
    print(f"  ✅ [UX Agent] UX 设计完成，核心流程数：{len(result.get('user_flows', []))}")
    return result


def design_system_agent(ctx: WorkflowContext) -> dict[str, Any]:
    """Design System Agent：颜色、字体、组件规范"""
    print("  🤖 [Design System Agent] 正在生成设计系统...")

    prd = ctx.phase_outputs["requirements"].get("prd", {})

    raw = _call_llm(
        system="""你是一位视觉设计专家。根据产品定位生成设计系统规范。
输出必须是合法的 JSON：
{
  "brand_identity": {"tone": "...", "personality": ["..."]},
  "colors": {"primary": "#...", "secondary": "#...", "accent": "#...", "neutral": ["#..."], "semantic": {"success": "#...", "warning": "#...", "error": "#..."}},
  "typography": {"font_family": "...", "heading": {"h1": "...", "h2": "...", "h3": "..."}, "body": {"regular": "...", "small": "..."}},
  "spacing": {"base": "8px", "scale": ["4px", "8px", "16px", "24px", "32px", "48px"]},
  "components": [{"name": "...", "variants": ["..."], "states": ["default", "hover", "active", "disabled"]}],
  "design_tokens": {"border_radius": "...", "shadow": "...", "transition": "..."}
}""",
        user=f"产品名称：{prd.get('product_name', '未知')}\n产品定位：{prd.get('problem_statement', '')}\n目标用户：{prd.get('target_users', [])}",
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"raw": raw}

    ctx.phase_outputs["design"]["design_system"] = result
    print(f"  ✅ [Design System Agent] 设计系统生成完成")
    return result


# ═══════════════════════════════════════════════
#  Phase 3 — 技术架构 & 开发
# ═══════════════════════════════════════════════

def architect_agent(ctx: WorkflowContext) -> dict[str, Any]:
    """Architect Agent：技术栈、系统架构、API 规范、DB Schema"""
    print("  🤖 [Architect Agent] 正在设计技术架构...")

    prd = ctx.phase_outputs["requirements"].get("prd", {})
    features = prd.get("features", [])

    raw = _call_llm(
        system="""你是一位技术架构师。根据产品需求设计完整的技术方案。
输出必须是合法的 JSON：
{
  "tech_stack": {"frontend": "...", "backend": "...", "database": "...", "cache": "...", "cloud": "...", "devops": ["..."]},
  "architecture_pattern": "单体/微服务/Serverless/混合",
  "system_components": [{"name": "...", "role": "...", "tech": "..."}],
  "api_spec": [{"endpoint": "/api/...", "method": "GET/POST/PUT/DELETE", "description": "...", "request": {}, "response": {}}],
  "db_schema": [{"table": "...", "fields": [{"name": "...", "type": "...", "constraints": "..."}]}],
  "security": {"auth_method": "...", "encryption": "...", "rate_limiting": "..."},
  "scalability": {"caching_strategy": "...", "cdn": "...", "load_balancing": "..."}
}""",
        user=f"产品功能清单：{json.dumps(features, ensure_ascii=False)}\n\n请设计适合此产品的技术架构。",
        max_tokens=6000,
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"raw": raw}

    ctx.phase_outputs["architecture"] = result
    print(f"  ✅ [Architect Agent] 架构设计完成，API 端点数：{len(result.get('api_spec', []))}")
    return result


def developer_agent(ctx: WorkflowContext) -> dict[str, Any]:
    """Developer Agent：代码骨架生成"""
    print("  🤖 [Developer Agent] 正在生成代码框架...")

    arch = ctx.phase_outputs.get("architecture", {})
    prd = ctx.phase_outputs["requirements"].get("prd", {})

    raw = _call_llm(
        system="""你是一位全栈开发工程师。根据架构方案生成项目代码骨架。
输出必须是合法的 JSON：
{
  "project_structure": "目录结构（树状文本）",
  "key_files": [{"path": "...", "purpose": "...", "code_snippet": "关键代码片段"}],
  "dependencies": {"package_manager": "npm/pip/...", "packages": [{"name": "...", "version": "...", "purpose": "..."}]},
  "env_variables": [{"key": "...", "description": "...", "required": true}],
  "setup_commands": ["命令1", "命令2"],
  "cicd_config": "CI/CD 配置文件内容（YAML）"
}""",
        user=f"技术栈：{arch.get('tech_stack', {})}\nAPI 规范：{json.dumps(arch.get('api_spec', [])[:3], ensure_ascii=False)}\n产品名：{prd.get('product_name', '未知')}",
        max_tokens=6000,
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"raw": raw}

    ctx.phase_outputs["development"]["code"] = result
    print(f"  ✅ [Developer Agent] 代码框架生成完成")
    return result


def code_review_agent(ctx: WorkflowContext) -> dict[str, Any]:
    """Code Review Agent：代码质量审查"""
    print("  🤖 [Code Review Agent] 正在进行代码审查...")

    code = ctx.phase_outputs["development"].get("code", {})

    raw = _call_llm(
        system="""你是一位资深代码审查工程师。审查代码质量并给出改进建议。
输出必须是合法的 JSON：
{
  "overall_score": 0-100,
  "issues": [{"severity": "critical/high/medium/low", "category": "security/performance/maintainability/style", "description": "...", "recommendation": "..."}],
  "security_vulnerabilities": ["潜在安全问题"],
  "performance_suggestions": ["性能优化建议"],
  "best_practices": ["最佳实践建议"],
  "approval_status": "approved/needs_changes/rejected"
}""",
        user=f"待审查代码结构：{json.dumps(code, ensure_ascii=False)[:3000]}",
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"raw": raw}

    ctx.phase_outputs["development"]["review"] = result
    score = result.get("overall_score", "N/A")
    print(f"  ✅ [Code Review Agent] 审查完成，质量评分：{score}/100")
    return result


# ═══════════════════════════════════════════════
#  Phase 4 — 测试 & QA
# ═══════════════════════════════════════════════

def qa_agent(ctx: WorkflowContext) -> dict[str, Any]:
    """QA Agent：测试用例、测试计划、质量报告"""
    print("  🤖 [QA Agent] 正在生成测试方案...")

    features = ctx.phase_outputs["requirements"].get("prd", {}).get("features", [])
    api_spec = ctx.phase_outputs.get("architecture", {}).get("api_spec", [])

    raw = _call_llm(
        system="""你是一位 QA 工程师。根据功能需求和 API 规范生成完整测试方案。
输出必须是合法的 JSON：
{
  "test_plan": {"scope": "...", "approach": "...", "environments": ["dev", "staging", "prod"]},
  "unit_tests": [{"module": "...", "test_cases": [{"name": "...", "input": "...", "expected": "..."}]}],
  "integration_tests": [{"scenario": "...", "steps": ["..."], "expected_result": "..."}],
  "api_tests": [{"endpoint": "...", "method": "...", "test_cases": [{"name": "...", "payload": {}, "expected_status": 200}]}],
  "e2e_tests": [{"user_flow": "...", "steps": ["..."], "assertions": ["..."]}],
  "quality_score": 0-100,
  "risk_areas": ["高风险区域1", "高风险区域2"]
}""",
        user=f"功能列表：{json.dumps(features, ensure_ascii=False)}\nAPI 规范（前3个）：{json.dumps(api_spec[:3], ensure_ascii=False)}",
        max_tokens=5000,
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"raw": raw}

    ctx.phase_outputs["qa"] = result
    print(f"  ✅ [QA Agent] 测试方案完成，质量评分：{result.get('quality_score', 'N/A')}/100")
    return result


def launch_agent(ctx: WorkflowContext) -> dict[str, Any]:
    """Launch Agent：上线 Checklist、部署文档、监控方案"""
    print("  🤖 [Launch Agent] 正在生成上线方案...")

    prd = ctx.phase_outputs["requirements"].get("prd", {})
    tech = ctx.phase_outputs.get("architecture", {}).get("tech_stack", {})
    qa = ctx.phase_outputs.get("qa", {})

    raw = _call_llm(
        system="""你是一位发布工程师。生成完整的产品上线方案。
输出必须是合法的 JSON：
{
  "pre_launch_checklist": [{"category": "...", "items": [{"task": "...", "owner": "...", "status": "pending"}]}],
  "deployment_steps": ["步骤1", "步骤2"],
  "rollback_plan": {"trigger_condition": "...", "steps": ["..."]},
  "monitoring": {"metrics": ["关键指标"], "alerts": [{"metric": "...", "threshold": "...", "action": "..."}], "dashboards": ["..."]},
  "post_launch_plan": {"day_1": ["...", "..."], "week_1": ["..."], "month_1": ["..."]},
  "launch_readiness_score": 0-100
}""",
        user=f"产品名：{prd.get('product_name', '未知')}\n技术栈：{json.dumps(tech, ensure_ascii=False)}\n测试质量分：{qa.get('quality_score', 'N/A')}\n风险区域：{qa.get('risk_areas', [])}",
        max_tokens=4000,
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(m.group()) if m else {"raw": raw}

    ctx.phase_outputs["launch"] = result
    score = result.get("launch_readiness_score", "N/A")
    print(f"  ✅ [Launch Agent] 上线方案完成，上线就绪评分：{score}/100")
    return result
