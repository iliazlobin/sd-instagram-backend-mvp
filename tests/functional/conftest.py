"""Helpers for in-process endpoint scenario tests.

These use the async ASGI `client` fixture (tests/conftest.py) against a real
Postgres (the CI `unit` job's postgres service). Each test mints fresh users
with unique usernames, so the shared DB needs no cleanup between tests.

Post creation validates only presence + size (<=10 MB), not real JPEG bytes,
so a tiny blob is a valid image.
"""

import io
import uuid

SMALL_IMAGE = b"\xff\xd8\xff\xe0" + b"\x00" * 64
OVERSIZED_IMAGE = b"\x00" * (11 * 1024 * 1024)


async def create_user(client, name="user"):
    r = await client.post(
        "/users",
        json={"username": f"{name}_{uuid.uuid4().hex[:8]}", "display_name": name.title()},
    )
    assert r.status_code == 201, r.text
    return r.json()["user_id"]


async def create_post(client, user_id, caption="hello #sunset"):
    r = await client.post(
        "/posts",
        files={"image": ("p.jpg", io.BytesIO(SMALL_IMAGE), "image/jpeg")},
        data={"caption": caption},
        headers={"X-User-Id": user_id},
    )
    assert r.status_code == 201, r.text
    return r.json()
