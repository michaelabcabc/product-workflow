"""
main.py — 产品工作流入口
用法：
    python main.py                          # 使用内置示例需求
    python main.py "你的产品需求描述..."    # 自定义需求
"""

import sys
import json
from orchestrator import run_workflow, generate_report


# ─── 示例需求（可替换为任意产品描述）────────────────
DEFAULT_BRIEF = """
开发一款面向自由职业者的时间追踪与发票管理 SaaS 产品。
核心功能包括：项目和客户管理、计时器（秒表+手动录入）、
多币种发票自动生成与 PDF 导出、银行对账、税务报表生成，
以及基于数据的收入分析仪表盘。目标用户是设计师、程序员等
独立从业者，希望用最少时间完成财务管理工作。
"""


def print_summary(ctx) -> None:
    """在终端打印关键输出摘要"""

    req = ctx.phase_outputs.get("requirements", {})
    prd = req.get("prd", {})
    design = ctx.phase_outputs.get("design", {})
    arch = ctx.phase_outputs.get("architecture", {})
    qa = ctx.phase_outputs.get("qa", {})
    launch = ctx.phase_outputs.get("launch", {})

    sep = "─" * 56

    print(f"\n{'═'*56}")
    print(f"  📦  产品：{prd.get('product_name', '未知')}")
    print(f"{'═'*56}")

    print(f"\n[需求阶段]")
    print(sep)
    features = prd.get("features", [])
    for f in features[:5]:
        print(f"  • [{f.get('priority','?')}] {f.get('name','')} — {f.get('description','')[:50]}")
    if len(features) > 5:
        print(f"  ... 共 {len(features)} 个功能")

    print(f"\n[技术架构]")
    print(sep)
    tech = arch.get("tech_stack", {})
    for k, v in tech.items():
        print(f"  {k:<12}: {v}")

    api_count = len(arch.get("api_spec", []))
    db_count = len(arch.get("db_schema", []))
    print(f"  API 端点     : {api_count} 个")
    print(f"  DB 数据表    : {db_count} 个")

    print(f"\n[测试 & 质量]")
    print(sep)
    print(f"  质量评分     : {qa.get('quality_score', 'N/A')}/100")
    risk = qa.get("risk_areas", [])
    for r in risk[:3]:
        print(f"  ⚠️  风险区域  : {r}")

    print(f"\n[上线就绪]")
    print(sep)
    print(f"  就绪评分     : {launch.get('launch_readiness_score', 'N/A')}/100")
    checklist = launch.get("pre_launch_checklist", [])
    print(f"  Checklist 项  : {sum(len(c.get('items',[])) for c in checklist)} 条")

    errors = ctx.workflow_status.get("errors", [])
    if errors:
        print(f"\n⚠️  工作流错误：{len(errors)} 个")
        for e in errors:
            print(f"   - {e['agent']}: {e['error']}")

    print(f"\n{'═'*56}\n")


if __name__ == "__main__":
    # 从命令行接收自定义需求，否则使用默认
    brief = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else DEFAULT_BRIEF.strip()

    # 运行工作流（parallel=True 为并行模式，可改为 False）
    ctx = run_workflow(brief, parallel=True)

    # 打印摘要
    print_summary(ctx)

    # 保存完整报告
    generate_report(ctx, "workflow_report.json")

    print("🎉  完成！查看 workflow_report.json 获取完整输出。")
