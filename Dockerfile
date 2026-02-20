FROM node:18-alpine AS frontend-build
WORKDIR /app
RUN npm config set registry https://registry.npmmirror.com
COPY frontend/package.json frontend/package-lock.json* ./frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend/ /app/frontend/
RUN npm run build

FROM python:3.12-slim AS backend-runtime
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN sed -i 's@deb.debian.org@mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list \
    && apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY backend/ /app/backend/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

WORKDIR /app/backend
RUN uv pip install --system -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

ENV MYSQL_HOST=mysql
ENV MYSQL_PORT=3306
ENV MYSQL_USER=root
ENV MYSQL_PASSWORD=12345678
ENV MYSQL_DATABASE=innerQaSystem
ENV MILVUS_HOST=milvus
ENV MILVUS_PORT=19530
ENV MILVUS_DATABASE=itcast
ENV MILVUS_COLLECTION=innerQA

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

