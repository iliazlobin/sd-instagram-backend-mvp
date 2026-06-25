"""FR-1: Create a post — upload a photo with caption and hashtags.

AC-1: POST /posts multipart form with image + caption "Sunset at the beach #sunset #beach"
      → 201 {post_id, media_url, hashtags: ["sunset", "beach"]}.
      Missing image → 422. Image >10MB → 413.
"""

import io

from verify.acceptance.conftest import (
    MINIMAL_JPEG,
    OVERSIZED_BLOB,
    assert_201,
    assert_413,
    assert_422,
    create_user,
)


def test_create_post_success(client):
    """Upload a photo with hashtags in caption → 201 with extracted hashtags."""
    user = create_user(client, "poster1", "Poster One")
    user_id = user["user_id"]

    r = client.post(
        "/posts",
        files={"image": ("sunset.jpg", io.BytesIO(MINIMAL_JPEG), "image/jpeg")},
        data={"caption": "Sunset at the beach #sunset #beach"},
        headers={"X-User-Id": user_id},
    )
    body = assert_201(r)

    assert "post_id" in body
    assert isinstance(body["post_id"], str) and len(body["post_id"]) > 0
    assert body["user_id"] == user_id
    assert body["caption"] == "Sunset at the beach #sunset #beach"
    assert "media_url" in body
    assert body["media_url"].startswith("/media/")
    assert body["media_type"] == "photo"
    assert body["like_count"] == 0
    assert "created_at" in body

    # Hashtags extracted and lowercased
    assert "hashtags" in body
    assert isinstance(body["hashtags"], list)
    assert set(body["hashtags"]) == {"sunset", "beach"}


def test_create_post_hashtags_deduplicated(client):
    """Duplicate hashtags in caption → deduplicated in output."""
    user = create_user(client, "poster2", "Poster Two")
    user_id = user["user_id"]

    r = client.post(
        "/posts",
        files={"image": ("test.jpg", io.BytesIO(MINIMAL_JPEG), "image/jpeg")},
        data={"caption": "Love #sunset and more #sunset #SUNSET"},
        headers={"X-User-Id": user_id},
    )
    body = assert_201(r)

    # All variations map to lowercase "sunset", deduplicated
    assert body["hashtags"] == ["sunset"]


def test_create_post_no_hashtags(client):
    """Caption without hashtags → empty hashtags array."""
    user = create_user(client, "poster3", "Poster Three")
    user_id = user["user_id"]

    r = client.post(
        "/posts",
        files={"image": ("test.jpg", io.BytesIO(MINIMAL_JPEG), "image/jpeg")},
        data={"caption": "Just a plain caption"},
        headers={"X-User-Id": user_id},
    )
    body = assert_201(r)

    assert body["hashtags"] == []


def test_create_post_missing_image(client):
    """Missing image file → 422."""
    user = create_user(client, "poster4", "Poster Four")
    user_id = user["user_id"]

    r = client.post(
        "/posts",
        data={"caption": "No image here"},
        headers={"X-User-Id": user_id},
    )
    assert_422(r)


def test_create_post_missing_caption(client):
    """Missing caption field → 422."""
    user = create_user(client, "poster5", "Poster Five")
    user_id = user["user_id"]

    r = client.post(
        "/posts",
        files={"image": ("test.jpg", io.BytesIO(MINIMAL_JPEG), "image/jpeg")},
        headers={"X-User-Id": user_id},
    )
    assert_422(r)


def test_create_post_missing_user_id(client):
    """Missing X-User-Id header → 422."""
    r = client.post(
        "/posts",
        files={"image": ("test.jpg", io.BytesIO(MINIMAL_JPEG), "image/jpeg")},
        data={"caption": "No user header"},
    )
    assert_422(r)


def test_create_post_oversized_image(client):
    """Image >10MB → 413."""
    user = create_user(client, "poster6", "Poster Six")
    user_id = user["user_id"]

    r = client.post(
        "/posts",
        files={"image": ("big.jpg", io.BytesIO(OVERSIZED_BLOB), "image/jpeg")},
        data={"caption": "Too big #fail"},
        headers={"X-User-Id": user_id},
    )
    assert_413(r)
