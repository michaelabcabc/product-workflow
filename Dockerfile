# ── 基础镜像 ──────────────────────────────────
FROM python:3.11-slim

# ── 工作目录 ──────────────────────────────────
WORKDIR /app

# ── 安装依赖（先复制 requirements 利用缓存层）──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 复制源码 ──────────────────────────────────
COPY . .

# ── 创建报告目录 ──────────────────────────────
RUN mkdir -p reports

# ── 暴露端口 ──────────────────────────────────
EXPOSE 8000

# ── 启动命令 ──────────────────────────────────
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
