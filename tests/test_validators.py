"""
Unit test stubs for `src.validators`.

These placeholders ensure the consistency checker API is present.
Concrete discrepancy tests can be added once `ConsolidatedRecord`
creation is implemented.
"""
from src.validators import ConsistencyChecker


def test_consistency_checker_api():
    cc = ConsistencyChecker()
    assert hasattr(cc, "find_discrepancies")
