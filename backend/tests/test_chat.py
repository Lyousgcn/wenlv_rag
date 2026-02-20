import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_flow(client: AsyncClient):
    username = "chat_user"
    password = "chat_password"

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

    # 创建会话
    session_resp = await client.post(
        "/api/chat/sessions",
        json={"name": "测试会话"},
        headers=headers,
    )
    assert session_resp.status_code == 200
    s_body = session_resp.json()
    assert s_body["code"] == 0
    session_id = s_body["data"]["id"]

    # 发起对话（使用模拟回答）
    chat_resp = await client.post(
        "/api/chat/stream",
        json={
            "session_id": session_id,
            "kb_ids": [],
            "question": "测试问题",
            "temperature": 0.8,
            "top_p": 0.8,
            "max_tokens": 32,
        },
        headers=headers,
    )
    assert chat_resp.status_code == 200
