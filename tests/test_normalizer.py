"""
Unit test stubs for `src.normalizer`.

Focus: ensure API for normalization and ambiguity checks exists.
"""

from src.normalizer import LotNormalizer


def test_normalizer_api():
    ln = LotNormalizer()
    assert hasattr(ln, "normalize")
    assert hasattr(ln, "is_ambiguous")
