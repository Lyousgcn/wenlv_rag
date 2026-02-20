from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_document_flow(client: AsyncClient):
    # 注册并登录，获取token
    username = "kb_user"
    password = "kb_password"

    await client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
            "captcha_id": "",
            "captcha_code": "",
        },
    )
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["code"] == 0
    token = body["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 创建知识库
    kb_resp = await client.post(
        "/api/knowledge/bases",
        json={"name": "测试知识库", "description": "用于测试的知识库"},
        headers=headers,
    )
    assert kb_resp.status_code == 200
    kb_body = kb_resp.json()
    assert kb_body["code"] == 0
    kb_id = kb_body["data"]["id"]

    # 上传文档
    data_dir = Path(__file__).resolve().parents[2] / "data"
    file_path = next(data_dir.glob("*.pdf"))
    with file_path.open("rb") as f:
        files = {"file": (file_path.name, f, "application/pdf")}
        upload_resp = await client.post(
            f"/api/knowledge/bases/{kb_id}/documents",
            headers=headers,
            files=files,
        )
    assert upload_resp.status_code == 200
    upload_body = upload_resp.json()
    assert upload_body["code"] == 0
