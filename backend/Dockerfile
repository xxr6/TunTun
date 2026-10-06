FROM python:3.12-slim

WORKDIR /app

# 先装依赖（利用镜像层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini . 2>/dev/null || true
COPY alembic ./alembic 2>/dev/null || true

# 启动时执行迁移（alembic.ini 就绪后生效）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
