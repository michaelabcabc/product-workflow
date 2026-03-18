"""
Orchestrator — 编排总控
负责：任务调度（串行/并行）、Agent 调用、错误重试、进度汇报
"""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Any

from context import WorkflowContext
from agents import (
    product_manager_agent,
    market_research_agent,
    ux_designer_agent,
    design_system_agent,
    architect_agent,
    developer_agent,
    code_review_agent,
    qa_agent,
    launch_agent,
)


# ─────────────────────────────────────────────
#  内部：带重试的 Agent 调用
# ─────────────────────────────────────────────
def _run_agent(
    agent_fn: Callable,
    ctx: WorkflowContext,
    max_retries: int = 2,
) -> dict[str, Any]:
    name = agent_fn.__name__
    for attempt in range(1, max_retries + 1):
        try:
            result = agent_fn(ctx)
            ctx.mark_agent_done(name)
            return result
        except Exception as e:
            print(f"  ⚠️  [{name}] 第 {attempt} 次失败：{e}")
            if attempt == max_retries:
                ctx.workflow_status["errors"].append(
                    {"agent": name, "error": str(e)}
                )
                return {"error": str(e)}
            time.sleep(2 ** attempt)   # 指数退避


# ─────────────────────────────────────────────
#  内部：并行执行多个 Agent
# ─────────────────────────────────────────────
def _run_parallel(
    agents: list[Callable],
    ctx: WorkflowContext,
    max_workers: int = 3,
) -> dict[str, Any]:
    """并行调用多个 Agent，返回 {agent_name: result} 映射"""
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_run_agent, fn, ctx): fn.__name__
            for fn in agents
        }
        for future in as_completed(futures):
            name = futures[future]
            results[name] = future.result()
    return results


# ─────────────────────────────────────────────
#  主 Orchestrator
# ─────────────────────────────────────────────
def run_workflow(product_brief: str, parallel: bool = True) -> WorkflowContext:
    """
    启动完整的产品开发工作流。

    Args:
        product_brief: 用户的产品需求描述（自然语言）
        parallel:      是否启用并行模式（默认 True）

    Returns:
        WorkflowContext: 包含所有 Agent 输出的完整上下文
    """
    ctx = WorkflowContext(product_brief=product_brief)
    print(f"\n{'='*60}")
    print(f"🚀  产品工作流启动")
    print(f"    项目 ID : {ctx.project_id}")
    print(f"    需求摘要 : {product_brief[:80]}...")
    print(f"    并行模式 : {'开启' if parallel else '关闭'}")
    print(f"{'='*60}\n")

    # ── Phase 1：需求分析 ──────────────────────
    ctx.set_phase("requirements")
    print("📋  Phase 1 — 需求分析 & 产品设计")
    if parallel:
        _run_parallel([product_manager_agent, market_research_agent], ctx)
    else:
        _run_agent(product_manager_agent, ctx)
        _run_agent(market_research_agent, ctx)

    # ── Phase 2：UI/UX 设计 ────────────────────
    ctx.set_phase("design")
    print("\n🎨  Phase 2 — UI/UX 设计")
    if parallel:
        _run_parallel([ux_designer_agent, design_system_agent], ctx)
    else:
        _run_agent(ux_designer_agent, ctx)
        _run_agent(design_system_agent, ctx)

    # ── Phase 3：技术架构 & 开发 ───────────────
    ctx.set_phase("development")
    print("\n🏗️   Phase 3 — 技术架构 & 开发")
    # Architect 必须先完成，Developer 和 Code Review 可以流水线
    _run_agent(architect_agent, ctx)
    if parallel:
        # Developer 生成后才能 Review，但可以流水线
        _run_agent(developer_agent, ctx)
        _run_agent(code_review_agent, ctx)
    else:
        _run_agent(developer_agent, ctx)
        _run_agent(code_review_agent, ctx)

    # ── Phase 4：测试 & QA ─────────────────────
    ctx.set_phase("qa")
    print("\n🧪  Phase 4 — 测试 & QA")
    if parallel:
        _run_parallel([qa_agent, launch_agent], ctx)
    else:
        _run_agent(qa_agent, ctx)
        _run_agent(launch_agent, ctx)

    ctx.set_phase("completed")

    # ── 工作流完成汇报 ─────────────────────────
    total_time = round(time.time() - ctx.created_at, 1)
    errors = ctx.workflow_status.get("errors", [])

    print(f"\n{'='*60}")
    print(f"✅  工作流完成！总耗时：{total_time}s")
    print(f"    完成 Agent 数：{len(ctx.workflow_status['completed_agents'])}/8")
    if errors:
        print(f"    ⚠️  出现错误：{len(errors)} 个")
        for e in errors:
            print(f"       - {e['agent']}: {e['error']}")
    print(f"{'='*60}\n")

    return ctx


# ─────────────────────────────────────────────
#  报告生成
# ─────────────────────────────────────────────
def generate_report(ctx: WorkflowContext, output_path: str = "workflow_report.json"):
    """将工作流结果序列化为 JSON 报告"""
    report = {
        "project_id": ctx.project_id,
        "product_brief": ctx.product_brief,
        "workflow_status": ctx.workflow_status,
        "phase_outputs": ctx.phase_outputs,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄  报告已保存至：{output_path}")
    return report
