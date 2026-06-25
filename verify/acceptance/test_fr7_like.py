"""FR-7: Like a post — idempotent like/unlike with counter updates.

AC-7: POST /posts/{id}/like → 201 (first), 200 (already liked).
      GET /posts/{id} → like_count reflects likes.
      DELETE /posts/{id}/like → 204 (was liked).
      GET /posts/{id} → like_count decremented.
      Missing post → 404.
"""

from verify.acceptance.conftest import (
    assert_200,
    assert_201,
    assert_204,
    assert_404,
    create_post,
    create_user,
)


def test_like_success(client):
    """Like a post → 201. like_count increments."""
    poster = create_user(client, "like_a", "Poster A")
    liker = create_user(client, "like_b", "Liker B")

    post = create_post(client, poster["user_id"], "Cool photo #art")

    r = client.post(
        f"/posts/{post['post_id']}/like",
        headers={"X-User-Id": liker["user_id"]},
    )
    body = assert_201(r)
    assert body["post_id"] == post["post_id"]
    assert body["user_id"] == liker["user_id"]
    assert "created_at" in body

    # Verify like_count on the post
    updated = assert_200(client.get(f"/posts/{post['post_id']}"))
    assert updated["like_count"] == 1


def test_like_idempotent(client):
    """Liking the same post twice → 200 (idempotent). Count stays 1."""
    poster = create_user(client, "like_c", "Poster C")
    liker = create_user(client, "like_d", "Liker D")

    post = create_post(client, poster["user_id"], "Another photo #art")

    # First like → 201
    client.post(
        f"/posts/{post['post_id']}/like",
        headers={"X-User-Id": liker["user_id"]},
    )

    # Second like → 200
    r = client.post(
        f"/posts/{post['post_id']}/like",
        headers={"X-User-Id": liker["user_id"]},
    )
    assert_200(r)

    # like_count still 1
    updated = assert_200(client.get(f"/posts/{post['post_id']}"))
    assert updated["like_count"] == 1


def test_multiple_users_like(client):
    """Multiple users liking → like_count reflects all unique likes."""
    poster = create_user(client, "like_e", "Poster E")
    u1 = create_user(client, "like_f", "Liker F")
    u2 = create_user(client, "like_g", "Liker G")
    u3 = create_user(client, "like_h", "Liker H")

    post = create_post(client, poster["user_id"], "Popular post #trending")

    for user_id in [u1["user_id"], u2["user_id"], u3["user_id"]]:
        client.post(
            f"/posts/{post['post_id']}/like",
            headers={"X-User-Id": user_id},
        )

    updated = assert_200(client.get(f"/posts/{post['post_id']}"))
    assert updated["like_count"] == 3


def test_unlike_success(client):
    """Unlike a liked post → 204. like_count decrements."""
    poster = create_user(client, "like_i", "Poster I")
    liker = create_user(client, "like_j", "Liker J")

    post = create_post(client, poster["user_id"], "Temporary like")

    # Like
    client.post(
        f"/posts/{post['post_id']}/like",
        headers={"X-User-Id": liker["user_id"]},
    )

    # Unlike
    r = client.delete(
        f"/posts/{post['post_id']}/like",
        headers={"X-User-Id": liker["user_id"]},
    )
    assert_204(r)

    # like_count back to 0
    updated = assert_200(client.get(f"/posts/{post['post_id']}"))
    assert updated["like_count"] == 0


def test_unlike_not_liked(client):
    """Unlike when not liked → 404."""
    poster = create_user(client, "like_k", "Poster K")
    liker = create_user(client, "like_l", "Liker L")

    post = create_post(client, poster["user_id"], "Never liked")

    r = client.delete(
        f"/posts/{post['post_id']}/like",
        headers={"X-User-Id": liker["user_id"]},
    )
    assert_404(r)


def test_like_nonexistent_post(client):
    """Like a non-existent post → 404."""
    liker = create_user(client, "like_m", "Liker M")

    r = client.post(
        "/posts/00000000-0000-0000-0000-000000000000/like",
        headers={"X-User-Id": liker["user_id"]},
    )
    assert_404(r)


def test_unlike_nonexistent_post(client):
    """Unlike a non-existent post → 404."""
    liker = create_user(client, "like_n", "Liker N")

    r = client.delete(
        "/posts/00000000-0000-0000-0000-000000000000/like",
        headers={"X-User-Id": liker["user_id"]},
    )
    assert_404(r)
