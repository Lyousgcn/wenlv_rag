import asyncio

import httpx


BASE = "http://127.0.0.1:8000"


async def main() -> None:
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            await client.post(
                f"{BASE}/api/auth/register",
                json={"username": "debug_user", "password": "debug_pass"},
            )
        except Exception:
            pass

        r = await client.post(
            f"{BASE}/api/auth/login",
            json={
                "username": "debug_user",
                "password": "debug_pass",
                "captcha_id": "",
                "captcha_code": "",
            },
        )
        print("login:", r.status_code, r.text)
        data = r.json()["data"]
        token = data["token"]
        headers = {"Authorization": f"Bearer {token}"}

        r2 = await client.post(
            f"{BASE}/api/chat/sessions",
            headers=headers,
            json={"name": "调试会话"},
        )
        print("session:", r2.status_code, r2.text)
        sid = r2.json()["data"]["id"]

        payload = {
            "session_id": sid,
            "kb_ids": [],
            "question": "调试一下流式回答是否正常。",
            "temperature": 0.8,
            "top_p": 0.8,
            "max_tokens": 64,
            "history_rounds": 3,
        }
        async with client.stream(
            "POST",
            f"{BASE}/api/chat/stream",
            headers=headers,
            json=payload,
        ) as resp:
            print("stream status:", resp.status_code)
            async for line in resp.aiter_lines():
                print("LINE:", repr(line))


if __name__ == "__main__":
    asyncio.run(main())

