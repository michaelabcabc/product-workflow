"""
app.py — FastAPI 服务层
提供：
  POST /run          手动触发工作流
  GET  /status/{id}  查询项目状态
  GET  /result/{id}  获取完整输出
  GET  /jobs         列出所有任务
  POST /cron/run     定时任务入口（由 Railway Cron 调用）
  GET  /health       健康检查
"""

import os
import json
import time
import threading
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator import run_workflow, generate_report
from context import WorkflowContext

app = FastAPI(
    title="Product Multi-Agent Workflow API",
    description="一键触发产品全流程 Multi-Agent 工作流",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 内存任务存储（生产环境可换成 Redis / PostgreSQL）──────
jobs: dict[str, dict] = {}


# ─────────────────────────────────────────────
#  数据模型
# ─────────────────────────────────────────────
class RunRequest(BaseModel):
    product_brief: str
    parallel: bool = True

class CronRequest(BaseModel):
    product_brief: Optional[str] = None
    secret: Optional[str] = None   # 简单鉴权


# ─────────────────────────────────────────────
#  后台任务：执行工作流
# ─────────────────────────────────────────────
def _execute_workflow(project_id: str, brief: str, parallel: bool):
    jobs[project_id]["status"] = "running"
    jobs[project_id]["started_at"] = datetime.utcnow().isoformat()
    try:
        ctx = run_workflow(brief, parallel=parallel)
        report = generate_report(ctx, f"reports/{project_id}.json")

        jobs[project_id]["status"] = "completed"
        jobs[project_id]["finished_at"] = datetime.utcnow().isoformat()
        jobs[project_id]["result_summary"] = _summarize(ctx)
        jobs[project_id]["report_path"] = f"reports/{project_id}.json"

    except Exception as e:
        jobs[project_id]["status"] = "failed"
        jobs[project_id]["error"] = str(e)
        jobs[project_id]["finished_at"] = datetime.utcnow().isoformat()


def _summarize(ctx: WorkflowContext) -> dict:
    prd = ctx.phase_outputs.get("requirements", {}).get("prd", {})
    arch = ctx.phase_outputs.get("architecture", {})
    qa = ctx.phase_outputs.get("qa", {})
    launch = ctx.phase_outputs.get("launch", {})
    return {
        "product_name": prd.get("product_name", ""),
        "feature_count": len(prd.get("features", [])),
        "api_count": len(arch.get("api_spec", [])),
        "quality_score": qa.get("quality_score"),
        "launch_readiness_score": launch.get("launch_readiness_score"),
        "completed_agents": ctx.workflow_status.get("completed_agents", []),
        "errors": ctx.workflow_status.get("errors", []),
    }


# ─────────────────────────────────────────────
#  API 路由
# ─────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/run", status_code=202)
def run(req: RunRequest, background_tasks: BackgroundTasks):
    """触发一次完整的产品工作流（异步执行，立即返回 project_id）"""
    from context import WorkflowContext
    import uuid
    project_id = str(uuid.uuid4())[:8]

    # 确保报告目录存在
    os.makedirs("reports", exist_ok=True)

    jobs[project_id] = {
        "project_id": project_id,
        "product_brief": req.product_brief[:200],
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "finished_at": None,
    }

    background_tasks.add_task(
        _execute_workflow, project_id, req.product_brief, req.parallel
    )

    return {
        "project_id": project_id,
        "status": "queued",
        "message": "工作流已加入队列，使用 /status/{project_id} 查询进度",
        "poll_url": f"/status/{project_id}",
    }


@app.get("/status/{project_id}")
def status(project_id: str):
    """查询工作流状态"""
    if project_id not in jobs:
        raise HTTPException(404, detail=f"未找到项目 {project_id}")
    job = jobs[project_id].copy()
    job.pop("result_summary", None)    # 状态接口不返回完整结果
    return job


@app.get("/result/{project_id}")
def result(project_id: str):
    """获取完整工作流输出（仅完成后可用）"""
    if project_id not in jobs:
        raise HTTPException(404, detail=f"未找到项目 {project_id}")
    job = jobs[project_id]
    if job["status"] != "completed":
        raise HTTPException(
            409, detail=f"任务尚未完成，当前状态：{job['status']}"
        )

    # 读取本地报告文件
    report_path = job.get("report_path")
    if report_path and os.path.exists(report_path):
        with open(report_path, encoding="utf-8") as f:
            return json.load(f)
    return job.get("result_summary", {})


@app.get("/jobs")
def list_jobs(limit: int = 20):
    """列出最近的工作流任务"""
    recent = sorted(jobs.values(), key=lambda j: j["created_at"], reverse=True)
    return {"total": len(jobs), "jobs": recent[:limit]}


@app.post("/cron/run")
def cron_run(req: CronRequest, background_tasks: BackgroundTasks):
    """
    定时任务入口 —— 由 Railway Cron Job 定时 POST 调用
    需要设置环境变量 CRON_SECRET 进行鉴权
    """
    expected = os.environ.get("CRON_SECRET", "")
    if expected and req.secret != expected:
        raise HTTPException(401, detail="无效的 CRON_SECRET")

    brief = req.product_brief or os.environ.get(
        "DEFAULT_BRIEF",
        "生成一份通用产品规格报告，作为每日工作流健康检查"
    )

    # 复用 /run 逻辑
    from fastapi import Request
    run_req = RunRequest(product_brief=brief, parallel=True)
    import uuid
    project_id = str(uuid.uuid4())[:8]
    os.makedirs("reports", exist_ok=True)
    jobs[project_id] = {
        "project_id": project_id,
        "product_brief": brief[:200],
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "trigger": "cron",
    }
    background_tasks.add_task(_execute_workflow, project_id, brief, True)
    return {"project_id": project_id, "trigger": "cron", "status": "queued"}
