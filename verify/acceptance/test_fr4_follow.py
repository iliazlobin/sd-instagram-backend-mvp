"""FR-4: Follow a user — idempotent follow/unfollow with counters.

AC-4: POST /users/{id}/follow → 201 (first), 200 (already following).
      Self-follow → 422.
      DELETE /users/{id}/follow → 204 (was following), 404 (wasn't).
"""

from verify.acceptance.conftest import (
    assert_200,
    assert_201,
    assert_204,
    assert_404,
    assert_422,
    create_user,
)


def test_follow_success(client):
    """Follow a user → 201. Verify follower/following counts updated."""
    alice = create_user(client, "follow_a", "Alice")
    bob = create_user(client, "follow_b", "Bob")

    r = client.post(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )
    body = assert_201(r)
    assert body["follower_id"] == alice["user_id"]
    assert body["followed_id"] == bob["user_id"]
    assert "created_at" in body

    # Verify counters
    alice_profile = assert_200(client.get(f"/users/{alice['user_id']}"))
    assert alice_profile["following_count"] == 1

    bob_profile = assert_200(client.get(f"/users/{bob['user_id']}"))
    assert bob_profile["follower_count"] == 1


def test_follow_idempotent(client):
    """Following the same user twice → 200 (idempotent). Counters unchanged."""
    alice = create_user(client, "follow_c", "Alice")
    bob = create_user(client, "follow_d", "Bob")

    # First follow → 201
    client.post(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )

    # Second follow → 200
    r = client.post(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )
    body = assert_200(r)
    assert body["follower_id"] == alice["user_id"]
    assert body["followed_id"] == bob["user_id"]

    # Counters still 1
    alice_profile = assert_200(client.get(f"/users/{alice['user_id']}"))
    assert alice_profile["following_count"] == 1

    bob_profile = assert_200(client.get(f"/users/{bob['user_id']}"))
    assert bob_profile["follower_count"] == 1


def test_self_follow_rejected(client):
    """Following yourself → 422."""
    alice = create_user(client, "follow_e", "Alice")

    r = client.post(
        f"/users/{alice['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )
    assert_422(r)


def test_unfollow_success(client):
    """Unfollow a followed user → 204. Counters decremented."""
    alice = create_user(client, "follow_f", "Alice")
    bob = create_user(client, "follow_g", "Bob")

    # Follow first
    client.post(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )

    # Unfollow
    r = client.delete(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )
    assert_204(r)

    # Counters back to 0
    alice_profile = assert_200(client.get(f"/users/{alice['user_id']}"))
    assert alice_profile["following_count"] == 0

    bob_profile = assert_200(client.get(f"/users/{bob['user_id']}"))
    assert bob_profile["follower_count"] == 0


def test_unfollow_twice_404(client):
    """Unfollowing when not following → 404."""
    alice = create_user(client, "follow_h", "Alice")
    bob = create_user(client, "follow_i", "Bob")

    # Never followed
    r = client.delete(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )
    assert_404(r)


def test_unfollow_after_unfollow_404(client):
    """Unfollow, then unfollow again → 404."""
    alice = create_user(client, "follow_j", "Alice")
    bob = create_user(client, "follow_k", "Bob")

    # Follow + unfollow
    client.post(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )
    client.delete(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )

    # Second unfollow → 404
    r = client.delete(
        f"/users/{bob['user_id']}/follow",
        headers={"X-User-Id": alice["user_id"]},
    )
    assert_404(r)


def test_follow_nonexistent_user(client):
    """Following a user that does not exist → 404."""
    alice = create_user(client, "follow_l", "Alice")

    r = client.post(
        "/users/00000000-0000-0000-0000-000000000000/follow",
        headers={"X-User-Id": alice["user_id"]},
    )
    assert_404(r)
