"""FR-6: Search by hashtag — GIN-indexed case-insensitive search.

AC-6: Create posts tagged #sunset and #beach.
      GET /search?q=sunset&type=hashtag → 200 + posts tagged #sunset.
      GET /search?q=nonexistent&type=hashtag → 200 [].
      Case-insensitive: Sunset matches sunset.
"""

from verify.acceptance.conftest import (
    assert_200,
    create_post,
    create_user,
)


def test_search_by_hashtag(client):
    """GET /search?q=sunset&type=hashtag → 200 with matching posts."""
    user = create_user(client, "search_a", "Searcher A")
    user_id = user["user_id"]

    sunset_post = create_post(client, user_id, "Golden hour #sunset")
    beach_post = create_post(client, user_id, "Ocean view #beach")

    r = client.get("/search", params={"q": "sunset", "type": "hashtag"})
    body = assert_200(r)

    assert isinstance(body, list)
    assert len(body) >= 1

    post_ids = [p["post_id"] for p in body]
    assert sunset_post["post_id"] in post_ids
    assert beach_post["post_id"] not in post_ids

    # Verify post shape in search results
    result = next(p for p in body if p["post_id"] == sunset_post["post_id"])
    assert result["caption"] == "Golden hour #sunset"
    assert "sunset" in result["hashtags"]


def test_search_no_results(client):
    """Hashtag with no matches → 200 with empty array."""
    r = client.get("/search", params={"q": "nonexistent", "type": "hashtag"})
    body = assert_200(r)
    assert body == []


def test_search_case_insensitive(client):
    """Search is case-insensitive: Sunset, SUNSET, sunset all match."""
    user = create_user(client, "search_b", "Searcher B")
    user_id = user["user_id"]

    post = create_post(client, user_id, "Beautiful evening #Sunset")

    # Lowercase query
    r = client.get("/search", params={"q": "sunset", "type": "hashtag"})
    body = assert_200(r)
    assert any(p["post_id"] == post["post_id"] for p in body)

    # Mixed case query
    r = client.get("/search", params={"q": "SunSet", "type": "hashtag"})
    body = assert_200(r)
    assert any(p["post_id"] == post["post_id"] for p in body)

    # Uppercase query
    r = client.get("/search", params={"q": "SUNSET", "type": "hashtag"})
    body = assert_200(r)
    assert any(p["post_id"] == post["post_id"] for p in body)


def test_search_pagination(client):
    """Search results support offset-based pagination."""
    user = create_user(client, "search_c", "Searcher C")
    user_id = user["user_id"]

    # Create 5 posts with #cat
    posts = []
    for i in range(5):
        p = create_post(client, user_id, f"Cat picture {i} #cat")
        posts.append(p)

    # Page 1
    r = client.get("/search", params={"q": "cat", "type": "hashtag", "limit": 3, "offset": 0})
    page1 = assert_200(r)
    assert len(page1) == 3

    # Page 2
    r = client.get("/search", params={"q": "cat", "type": "hashtag", "limit": 3, "offset": 3})
    page2 = assert_200(r)
    assert len(page2) == 2

    # All unique
    page1_ids = {p["post_id"] for p in page1}
    page2_ids = {p["post_id"] for p in page2}
    assert page1_ids.isdisjoint(page2_ids)


def test_search_multiple_hashtags(client):
    """A post with multiple hashtags is found by any of them."""
    user = create_user(client, "search_d", "Searcher D")
    user_id = user["user_id"]

    post = create_post(client, user_id, "Beach sunset #sunset #beach #vacation")

    # Find by first hashtag
    r = client.get("/search", params={"q": "sunset", "type": "hashtag"})
    assert any(p["post_id"] == post["post_id"] for p in assert_200(r))

    # Find by second hashtag
    r = client.get("/search", params={"q": "beach", "type": "hashtag"})
    assert any(p["post_id"] == post["post_id"] for p in assert_200(r))

    # Find by third hashtag
    r = client.get("/search", params={"q": "vacation", "type": "hashtag"})
    assert any(p["post_id"] == post["post_id"] for p in assert_200(r))
