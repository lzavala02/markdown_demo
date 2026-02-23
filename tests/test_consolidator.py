"""
Unit test stubs for `src.consolidator`.

These placeholders outline the expected consolidation API and
integration points (normalizer + matcher). Concrete assertions should be
added when implementations are available.
"""
from src.consolidator import DataConsolidator


def test_consolidator_api():
    dc = DataConsolidator()
    assert hasattr(dc, "consolidate")
