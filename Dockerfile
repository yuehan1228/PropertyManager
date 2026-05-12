FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENV DATABASE_URL=sqlite:///./fund_tracker.db
ENV TIMEZONE=Asia/Shanghai

EXPOSE 8000

# Zeabur / 标准 PaaS 会注入 PORT 环境变量
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
