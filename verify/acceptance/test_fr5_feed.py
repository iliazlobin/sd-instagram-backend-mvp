"""FR-5: Get feed — chronological feed from followed users, paginated via cursor.

AC-5: After user A follows B, and B creates a post,
      GET /feed for A → 200 + array containing B's post (newest first).
      Pagination via `before` cursor.
      User following no one → 200 [].
      Fan-out: B's post appears in A's feed after A follows B.
"""

from verify.acceptance.conftest import (
    assert_200,
    create_post,
    create_user,
)


def test_feed_with_followed_posts(client):
    """After A follows B, B's posts appear in A's feed."""
    alice = create_user(client, "feed_a", "Alice")
    bob = create_user(client, "feed_b", "Bob")

    # Alice follows Bob
    client.post(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )

    # Bob creates a post
    post = create_post(client, bob["user_id"], "Bob's first post #hello")

    # Alice's feed should contain Bob's post
    r = client.get("/feed", headers={"X-User-Id": alice["user_id"]})
    body = assert_200(r)

    assert isinstance(body, list)
    assert len(body) >= 1

    # Bob's post should be in the feed
    feed_post_ids = [p["post_id"] for p in body]
    assert post["post_id"] in feed_post_ids

    # Verify feed entry shape
    bob_post_in_feed = next(p for p in body if p["post_id"] == post["post_id"])
    assert bob_post_in_feed["caption"] == "Bob's first post #hello"
    assert "author" in bob_post_in_feed
    assert bob_post_in_feed["author"]["user_id"] == bob["user_id"]
    assert bob_post_in_feed["author"]["username"] == bob["username"]


def test_feed_fan_out_new_follower(client):
    """When A follows B, A sees B's recent posts (backfill)."""
    alice = create_user(client, "feed_c", "Alice")
    bob = create_user(client, "feed_d", "Bob")

    # Bob creates posts BEFORE Alice follows him
    post1 = create_post(client, bob["user_id"], "Bob post 1")
    post2 = create_post(client, bob["user_id"], "Bob post 2")

    # Alice follows Bob now
    client.post(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )

    # Alice's feed should contain Bob's recent posts (backfill)
    r = client.get("/feed", headers={"X-User-Id": alice["user_id"]})
    body = assert_200(r)

    feed_post_ids = [p["post_id"] for p in body]
    assert post2["post_id"] in feed_post_ids  # newest
    assert post1["post_id"] in feed_post_ids  # older


def test_feed_empty_when_following_no_one(client):
    """User following no one → 200 with empty array."""
    alice = create_user(client, "feed_e", "Alice")

    r = client.get("/feed", headers={"X-User-Id": alice["user_id"]})
    body = assert_200(r)

    assert body == []


def test_feed_no_self_posts(client):
    """A user's own posts do NOT appear in their feed (only followed users)."""
    alice = create_user(client, "feed_f", "Alice")

    # Alice posts something
    create_post(client, alice["user_id"], "My own post")

    # Alice's feed should not include her own post (she follows no one)
    r = client.get("/feed", headers={"X-User-Id": alice["user_id"]})
    body = assert_200(r)

    # Should be empty unless fan-out logic accidentally includes self
    alice_posts_in_feed = [
        p for p in body if p.get("author", {}).get("user_id") == alice["user_id"]
    ]
    assert len(alice_posts_in_feed) == 0


def test_feed_pagination_cursor(client):
    """Cursor-based pagination with `before` parameter."""
    alice = create_user(client, "feed_g", "Alice")
    bob = create_user(client, "feed_h", "Bob")

    client.post(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )

    # Bob creates 5 posts
    posts = []
    for i in range(5):
        p = create_post(client, bob["user_id"], f"Bob post {i}")
        posts.append(p)
    posts.reverse()  # newest first

    # First page: limit=3
    r = client.get("/feed?limit=3", headers={"X-User-Id": alice["user_id"]})
    page1 = assert_200(r)
    assert len(page1) == 3
    assert page1[0]["post_id"] == posts[0]["post_id"]

    # Second page: before=<cursor of last item from page1>
    cursor = page1[-1]["created_at"]
    r = client.get(
        f"/feed?limit=3&before={cursor}",
        headers={"X-User-Id": alice["user_id"]},
    )
    page2 = assert_200(r)
    assert len(page2) == 2  # 5 total - 3 from page1
    assert page2[0]["post_id"] == posts[3]["post_id"]
    assert page2[1]["post_id"] == posts[4]["post_id"]


def test_feed_only_shows_followed_users(client):
    """Feed does not include posts from users the current user doesn't follow."""
    alice = create_user(client, "feed_i", "Alice")
    bob = create_user(client, "feed_j", "Bob")
    charlie = create_user(client, "feed_k", "Charlie")

    # Alice follows Bob, but NOT Charlie
    client.post(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )

    # Both Bob and Charlie create posts
    bob_post = create_post(client, bob["user_id"], "Bob's post")
    charlie_post = create_post(client, charlie["user_id"], "Charlie's post")

    r = client.get("/feed", headers={"X-User-Id": alice["user_id"]})
    body = assert_200(r)

    feed_post_ids = [p["post_id"] for p in body]
    assert bob_post["post_id"] in feed_post_ids
    assert charlie_post["post_id"] not in feed_post_ids
