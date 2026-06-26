"""Functional endpoint scenarios (spec §6) — in-process against a real DB.

The important behaviours, not every case: idempotency, ownership, error paths,
search semantics. The black-box FR contract lives in verify/acceptance/.
"""

import io
import uuid

import pytest

from tests.functional.conftest import OVERSIZED_IMAGE, create_post, create_user


@pytest.mark.asyncio
async def test_like_is_idempotent(client):
    author = await create_user(client, "author")
    liker = await create_user(client, "liker")
    pid = (await create_post(client, author))["post_id"]

    first = await client.post(f"/posts/{pid}/like", headers={"X-User-Id": liker})
    assert first.status_code == 201
    again = await client.post(f"/posts/{pid}/like", headers={"X-User-Id": liker})
    assert again.status_code == 200  # idempotent — no second row

    detail = await client.get(f"/posts/{pid}")
    assert detail.json()["like_count"] == 1


@pytest.mark.asyncio
async def test_unlike_then_second_unlike_404(client):
    author = await create_user(client, "a")
    liker = await create_user(client, "b")
    pid = (await create_post(client, author))["post_id"]
    await client.post(f"/posts/{pid}/like", headers={"X-User-Id": liker})

    assert (
        await client.delete(f"/posts/{pid}/like", headers={"X-User-Id": liker})
    ).status_code == 204
    assert (
        await client.delete(f"/posts/{pid}/like", headers={"X-User-Id": liker})
    ).status_code == 404


@pytest.mark.asyncio
async def test_follow_is_idempotent(client):
    a = await create_user(client, "a")
    b = await create_user(client, "b")
    assert (await client.post(f"/users/{b}/follow", headers={"X-User-Id": a})).status_code == 201
    assert (await client.post(f"/users/{b}/follow", headers={"X-User-Id": a})).status_code == 200


@pytest.mark.asyncio
async def test_self_follow_rejected(client):
    me = await create_user(client, "me")
    assert (await client.post(f"/users/{me}/follow", headers={"X-User-Id": me})).status_code == 422


@pytest.mark.asyncio
async def test_image_over_10mb_rejected(client):
    user = await create_user(client, "big")
    r = await client.post(
        "/posts",
        files={"image": ("big.jpg", io.BytesIO(OVERSIZED_IMAGE), "image/jpeg")},
        data={"caption": "too big"},
        headers={"X-User-Id": user},
    )
    assert r.status_code == 413


@pytest.mark.asyncio
async def test_hashtag_search_is_case_insensitive(client):
    author = await create_user(client, "tagger")
    tag = uuid.uuid4().hex[:10]  # unique, so the result set is deterministic
    await create_post(client, author, caption=f"sunset vibes #{tag}")

    # stored lowercased; search with the UPPERCASE query still matches
    hit = await client.get(f"/search?q={tag.upper()}")
    assert hit.status_code == 200
    assert any(tag in p["hashtags"] for p in hit.json())

    miss = await client.get(f"/search?q={uuid.uuid4().hex[:10]}")
    assert miss.status_code == 200
    assert miss.json() == []


@pytest.mark.asyncio
async def test_unknown_ids_return_404(client):
    user = await create_user(client, "x")
    missing = str(uuid.uuid4())
    assert (await client.get(f"/posts/{missing}")).status_code == 404
    assert (
        await client.post(f"/posts/{missing}/like", headers={"X-User-Id": user})
    ).status_code == 404
