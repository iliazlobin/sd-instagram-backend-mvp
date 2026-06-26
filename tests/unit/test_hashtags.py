"""Unit tests for hashtag extraction — a pure function, no DB or IO."""

from instagram.services.post_service import extract_hashtags


def test_extracts_and_lowercases():
    assert extract_hashtags("Hello #Sunset at #Beach") == ["sunset", "beach"]


def test_deduplicates_preserving_order():
    assert extract_hashtags("#a #b #A #b #c") == ["a", "b", "c"]


def test_no_hashtags_returns_empty():
    assert extract_hashtags("just a plain caption, nothing tagged") == []


def test_stops_at_punctuation():
    assert extract_hashtags("#one, #two! #three.") == ["one", "two", "three"]
