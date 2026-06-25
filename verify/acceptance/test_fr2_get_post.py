"""FR-2: Get post detail — fetch full post by ID including all metadata.

AC-2: GET /posts/{id} → 200 + full post JSON (post_id, user_id, caption,
      media_url, hashtags[], like_count, created_at). Non-existent ID → 404.
"""

from verify.acceptance.conftest import (
    assert_200,
    assert_404,
    create_post,
    create_user,
)


def test_get_post_success(client):
    """GET /posts/{id} → 200 with full post metadata."""
    user = create_user(client, "viewer1", "Viewer One")
    user_id = user["user_id"]

    post = create_post(client, user_id, "A beautiful day #nature #sun")

    r = client.get(f"/posts/{post['post_id']}")
    body = assert_200(r)

    assert body["post_id"] == post["post_id"]
    assert body["user_id"] == user_id
    assert body["caption"] == "A beautiful day #nature #sun"
    assert body["media_url"] == post["media_url"]
    assert body["media_type"] == "photo"
    assert "hashtags" in body
    assert isinstance(body["hashtags"], list)
    assert set(body["hashtags"]) == {"nature", "sun"}
    assert body["like_count"] == 0
    assert "created_at" in body


def test_get_post_not_found(client):
    """GET /posts/{nonexistent} → 404."""
    r = client.get("/posts/00000000-0000-0000-0000-000000000000")
    assert_404(r)
