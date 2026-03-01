"""
Unit test stubs for `src.matcher`.

Outline the matcher API and ensure it returns diagnostic structures.
"""

from src.matcher import RecordMatcher


def test_matcher_api():
    rm = RecordMatcher()
    assert hasattr(rm, "match_by_lot")
