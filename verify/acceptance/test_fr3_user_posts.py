"""FR-3: List user posts — paginated reverse-chronological grid.

AC-3: GET /users/{id}/posts?limit=10&offset=0 → 200 + array of posts (newest first).
      User with no posts → 200 + []. Missing user → 404.
"""

from verify.acceptance.conftest import (
    assert_200,
    assert_404,
    create_post,
    create_user,
)


def test_user_posts_success(client):
    """GET /users/{id}/posts → 200 with array of posts."""
    user = create_user(client, "griduser1", "Grid User One")
    user_id = user["user_id"]

    # Create 3 posts
    p1 = create_post(client, user_id, "First post #one")
    p2 = create_post(client, user_id, "Second post #two")
    p3 = create_post(client, user_id, "Third post #three")

    r = client.get(f"/users/{user_id}/posts?limit=10&offset=0")
    body = assert_200(r)

    assert isinstance(body, list)
    assert len(body) == 3

    # Newest first
    post_ids = [p["post_id"] for p in body]
    assert post_ids == [p3["post_id"], p2["post_id"], p1["post_id"]]


def test_user_posts_empty(client):
    """User with no posts → 200 with empty array."""
    user = create_user(client, "griduser2", "Grid User Two")
    user_id = user["user_id"]

    r = client.get(f"/users/{user_id}/posts?limit=10&offset=0")
    body = assert_200(r)

    assert body == []


def test_user_posts_pagination(client):
    """Pagination via limit/offset returns correct slices."""
    user = create_user(client, "griduser3", "Grid User Three")
    user_id = user["user_id"]

    # Create 5 posts
    posts = []
    for i in range(5):
        p = create_post(client, user_id, f"Post {i}")
        posts.append(p)
    posts.reverse()  # Newest first for comparison

    # Page 1: limit=2, offset=0
    r = client.get(f"/users/{user_id}/posts?limit=2&offset=0")
    page1 = assert_200(r)
    assert len(page1) == 2
    assert page1[0]["post_id"] == posts[0]["post_id"]
    assert page1[1]["post_id"] == posts[1]["post_id"]

    # Page 2: limit=2, offset=2
    r = client.get(f"/users/{user_id}/posts?limit=2&offset=2")
    page2 = assert_200(r)
    assert len(page2) == 2
    assert page2[0]["post_id"] == posts[2]["post_id"]
    assert page2[1]["post_id"] == posts[3]["post_id"]

    # Page 3: limit=2, offset=4
    r = client.get(f"/users/{user_id}/posts?limit=2&offset=4")
    page3 = assert_200(r)
    assert len(page3) == 1
    assert page3[0]["post_id"] == posts[4]["post_id"]


def test_user_posts_user_not_found(client):
    """GET /users/{nonexistent}/posts → 404."""
    r = client.get("/users/00000000-0000-0000-0000-000000000000/posts")
    assert_404(r)
