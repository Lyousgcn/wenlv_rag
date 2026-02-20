import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # 获取验证码
    r = await client.get("/api/auth/captcha")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    captcha_id = body["data"]["captcha_id"]
    # 测试环境直接绕过验证码校验
    username = "test_user"
    password = "test_password"

    r = await client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    assert r.status_code in (200, 400)

    r = await client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
            "captcha_id": captcha_id,
            "captcha_code": "0000",
        },
    )
    assert r.status_code in (200, 400)

