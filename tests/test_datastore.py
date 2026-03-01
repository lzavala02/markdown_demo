"""
Unit test stubs for `src.datastore`.

These tests check the in-memory datastore API surface so consumers can
write tests against a stable repository interface.
"""

from src.datastore import InMemoryDataStore


def test_datastore_api():
    ds = InMemoryDataStore()
    assert hasattr(ds, "save_records")
    assert hasattr(ds, "query_by_lot")
    assert hasattr(ds, "query_by_date_range")
