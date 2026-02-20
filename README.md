# 文旅智能问答系统（基于企业内容知识的 RAG 应用）

本项目是一套面向文旅行业的智能问答系统，基于 RAG（检索增强生成）技术，为游客提供可信、可追溯的旅游咨询服务。系统支持知识库管理、文档解析向量化、对话会话管理等功能，并通过 Docker 一键部署到云服务器。

## 项目结构

- `frontend/`：基于 Vue 3 + Vite 的前端单页应用
- `backend/`：基于 FastAPI 的后端服务
  - `app/`：业务代码（路由、模型、服务）
  - `sql/init.sql`：MySQL 初始化建表脚本
- `data/`：示例文档与持久化数据目录（挂载 MySQL / Milvus 数据）
- `Dockerfile`：前后端多阶段构建镜像
- `docker-compose.yml`：应用 + MySQL + Milvus 编排配置
- `start.sh`：一键启动/停止/重启/查看日志脚本

## 核心功能概览

- 用户模块：注册、登录、JWT 鉴权、图形验证码
- 知识库模块：知识库管理、文件上传、解析、切块、向量化、预览与编辑
- 问答模块：基于 Milvus 检索的 RAG，对接通义千问（qwen-max），支持流式输出与会话记忆
- 配置模块：通过环境变量和 `.env` 模板统一管理 MySQL、Milvus、大模型参数

## 环境变量配置

### 后端配置（backend/.env.example）

复制示例文件：

```bash
cp backend/.env.example backend/.env
```

需要重点修改：

- `QWEN_API_KEY`：通义千问 API Key
- `JWT_SECRET_KEY`：JWT 签名密钥（请改为高强度随机字符串）

其余 MySQL / Milvus 参数与 `docker-compose.yml` 中保持一致即可。

### 前端配置（frontend/.env.example）

```bash
cp frontend/.env.example frontend/.env
```

默认：

- `VITE_API_BASE=/api`（由后端统一反向代理，无需额外修改）

## 本地开发启动方式（可选）

### 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问地址：

- 前端开发环境：http://localhost:5173
- 后端接口：http://localhost:8000/api

## Docker 一键部署

### 前置准备

1. 服务器安装 Docker 与 docker-compose
2. 放通服务器 80 端口（安全组/防火墙）

### 部署步骤

```bash
git clone <你的仓库地址> wenlv_rag
cd wenlv_rag

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 修改 backend/.env 中的 QWEN_API_KEY、JWT_SECRET_KEY 等

chmod +x start.sh
./start.sh start
```

等待镜像构建并启动（首次时间略长），之后可通过：

- 查看服务状态：`docker-compose ps`
- 查看应用日志：`./start.sh logs`

### 公网访问

部署成功后，可通过以下地址访问：

- `http://服务器IP:80`

例如：`http://1.2.3.4:80`

## docker-compose 服务说明

- `app`：前端静态资源 + FastAPI 后端服务（容器内端口 8000，映射为宿主机 80）
- `mysql`：MySQL 8.0 数据库（只在内部网络暴露）
- `milvus-etcd` / `milvus-minio` / `milvus-standalone`：Milvus 2.x 及其依赖

数据持久化目录：

- MySQL 数据：`./data/mysql`
- Milvus 数据：`./data/milvus`

## 测试说明

后端使用 `pytest` 作为测试框架，测试用例位于 `backend/tests/` 目录。

执行测试：

```bash
cd backend
pytest
```

覆盖内容包括：

- 用户注册与登录流程
- 文档上传 → 解析 → 向量化流程（依赖 Milvus / MySQL）
- 会话创建与问答调用（通义千问未配置时使用模拟流式返回）

> 提示：如在本地没有启动 MySQL / Milvus，对应集成测试可能会被跳过或失败，请在 Docker 环境中运行以获得完整覆盖。

## 主要接口约定

- 统一前缀：`/api`
- 统一返回格式：

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

`code = 0` 表示成功，其余为业务异常。

## 安全与配置建议

- 不要在代码中写死任何密钥和密码，统一通过环境变量注入
- 生产环境请务必修改：
  - `MYSQL_ROOT_PASSWORD`
  - `JWT_SECRET_KEY`
  - `QWEN_API_KEY`
- 如需 HTTPS，请在云厂商或 Nginx 层配置 TLS 终端

## 常见问题

1. **容器启动失败，提示无法连接 MySQL 或 Milvus？**
   - 使用 `docker-compose ps` 检查 `mysql`、`milvus-standalone` 状态
   - 确认服务器内存不少于 4G（建议 8G）

2. **访问页面空白或接口 404？**
   - 确认 `app` 服务状态为 `Up`
   - 查看 `./start.sh logs`，检查 uvicorn 日志是否报错

3. **通义千问无返回或报鉴权失败？**
   - 检查 `backend/.env` 与 `docker-compose.yml` 中的 `QWEN_API_KEY` 是否一致且正确

