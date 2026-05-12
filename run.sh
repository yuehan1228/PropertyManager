#!/bin/bash
# 启动个人资产追踪系统后端
set -e

cd "$(dirname "$0")/backend"

# 自动创建 venv（若不存在）
if [ ! -d ".venv" ]; then
    echo "→ 创建虚拟环境..."
    python3 -m venv .venv
fi

source ~/miniconda3/bin/activate

# 安装依赖
echo "→ 安装依赖..."
pip install -q -r requirements.txt

# 启动
echo "→ 启动服务 (http://0.0.0.0:8000)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
