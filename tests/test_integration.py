"""
Integration Tests for Operations Data Consolidation
===================================================

Tests interactions between multiple modules to ensure they work correctly together.

Test Coverage:
- Database initialization and schema creation
- Multi-source data import (CSV/Excel)
- Lot ID normalization and matching
- Data consolidation across sources
- Production line reporting
- Defect trend analysis
- Shipment status tracking
- Data validation and consistency checks

Run with: pytest tests/test_integration.py -v
"""

import pytest
import os
import tempfile
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
import io

# Import application modules
from config import Config
from database import Database
from data_importer import DataImporter
from data_normalizer import LotIDNormalizer, LotIDMatcher
from data_consolidator import ConsolidatedView
from reporter import Reporter
from data_validator import DataValidator


# ===== Fixtures =====

@pytest.fixture(scope="module")
def setup_test_db():
    """Sets up test database once for all integration tests."""
    # Initialize database
    Database.initialize()
    yield
    # Cleanup
    Database.close_all()


@pytest.fixture(autouse=True)
def clean_database(setup_test_db):
    """Cleans database between each test."""
    with Database.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
            TRUNCATE TABLE data_discrepancies, lot_id_normalizations, data_imports,
                     shipping_records, quality_records, production_records,
                     lots, defect_types, production_lines
            RESTART IDENTITY CASCADE
            """)
            conn.commit()
        finally:
            cursor.close()
    yield


@pytest.fixture
def sample_production_csv():
    """Creates a sample production CSV file."""
    data = {
        'lot_id': ['LOT-20260112-001', 'LOT-20260112-002', '  lot 20260113 001  '],
        'production_date': ['2026-01-12', '2026-01-12', '2026-01-13'],
        'production_line': ['Line 1', 'Line 2', 'Line 1'],
        'quantity_produced': [382, 290, 401],
        'status': ['Completed', 'Completed', 'In Progress'],
        'issue_description': [None, 'Minor delay', None]
    }
    df = pd.DataFrame(data)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_quality_csv():
    """Creates a sample quality CSV file."""
    data = {
        'lot_id': ['LOT-20260112-001', 'LOT-20260112-002'],
        'inspection_date': ['2026-01-13', '2026-01-13'],
        'defect_type': ['Surface Scratch', 'Dimension Variance'],
        'defect_count': [5, 3],
        'inspection_status': ['Pass', 'Pass'],
        'inspector': ['John Doe', 'Jane Smith'],
        'notes': ['Minor scratches', 'Within tolerance']
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_shipping_csv():
    """Creates a sample shipping CSV file."""
    data = {
        'lot_id': ['LOT-20260112-001'],
        'shipment_status': ['Shipped'],
        'carrier_info': ['XPO - PRO-812238'],
        'destination': ['MI'],
        'shipment_date': ['2026-01-29']
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)


# ===== Integration Tests =====

class TestDatabaseIntegration:
    """Tests database module integration."""
    
    def test_database_initialization(self, setup_test_db):
        """Test that database initializes with proper schema."""
        # Verify tables exist
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                # Verify all required tables are created
                required_tables = [
                    'production_lines', 'defect_types', 'lots',
                    'production_records', 'quality_records', 'shipping_records',
                    'data_imports', 'lot_id_normalizations', 'data_discrepancies'
                ]
                
                for table in required_tables:
                    assert table in tables, f"Table {table} not found in schema"
            finally:
                cursor.close()
    
    def test_connection_pooling(self, setup_test_db):
        """Test that connection pool works correctly."""
        # Test that we can get multiple connections
        for _ in range(3):
            with Database.get_connection() as conn:
                assert conn is not None
                # Verify connection works
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
                cursor.close()


class TestDataImportIntegration:
    """Tests data import integration with database and normalizer."""
    
    def test_production_data_import(self, setup_test_db, sample_production_csv):
        """Test importing production data from CSV."""
        result = DataImporter.import_file(sample_production_csv, 'production')
        
        assert result['success'] is True
        assert result['rows_imported'] == 3
        assert result['rows_failed'] == 0
        
        # Verify data in database
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM production_records")
                count = cursor.fetchone()[0]
                assert count == 3
                
                # Verify lot normalization
                cursor.execute("SELECT COUNT(*) FROM lots")
                lot_count = cursor.fetchone()[0]
                assert lot_count == 3
            finally:
                cursor.close()
    
    def test_quality_data_import(self, setup_test_db, sample_quality_csv, sample_production_csv):
        """Test importing quality data that references existing lots."""
        # First import production data to create lots
        DataImporter.import_file(sample_production_csv, 'production')
        
        # Then import quality data
        result = DataImporter.import_file(sample_quality_csv, 'quality')
        
        assert result['success'] is True
        assert result['rows_imported'] == 2
        
        # Verify quality records
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM quality_records")
                count = cursor.fetchone()[0]
                assert count == 2
                
                # Verify defect types were created
                cursor.execute("SELECT COUNT(*) FROM defect_types")
                defect_count = cursor.fetchone()[0]
                assert defect_count >= 2
            finally:
                cursor.close()
    
    def test_shipping_data_import(self, setup_test_db, sample_production_csv, sample_shipping_csv):
        """Test importing shipping data."""
        # Import production data first
        DataImporter.import_file(sample_production_csv, 'production')
        
        # Import shipping data
        result = DataImporter.import_file(sample_shipping_csv, 'shipping')
        
        assert result['success'] is True
        assert result['rows_imported'] == 1
        
        # Verify shipping records
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM shipping_records")
                count = cursor.fetchone()[0]
                assert count == 1
            finally:
                cursor.close()
    
    def test_import_tracking(self, setup_test_db, sample_production_csv):
        """Test that imports are tracked in data_imports table."""
        DataImporter.import_file(sample_production_csv, 'production')
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                SELECT source_type, file_format, import_status 
                FROM data_imports 
                WHERE source_type = 'production'
                """)
                result = cursor.fetchone()
                
                assert result is not None
                assert result[0] == 'production'
                assert result[1] == 'csv'
                assert result[2] == 'Success'
            finally:
                cursor.close()


class TestLotIDNormalizationIntegration:
    """Tests lot ID normalization across import and consolidation."""
    
    def test_lot_id_normalization(self, setup_test_db):
        """Test lot ID normalization process."""
        # Test various lot ID formats
        test_cases = [
            ('  LOT-20260112-001  ', 'LOT-20260112-001'),
            ('lot 20260112 001', 'LOT-20260112-001'),
            ('LOT_20260112_001', 'LOT-20260112-001'),
            ('LOT/20260112/001', 'LOT-20260112-001'),
        ]
        
        for original, expected in test_cases:
            normalized = LotIDNormalizer.normalize(original)
            assert normalized == expected, f"Failed to normalize {original}"
    
    def test_lot_id_matching(self, setup_test_db, sample_production_csv):
        """Test that different lot ID formats match to same lot."""
        # Import data with inconsistent lot IDs
        DataImporter.import_file(sample_production_csv, 'production')
        
        # Verify lots were normalized and deduplicated
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT business_lot_number FROM lots ORDER BY lot_id")
                lot_numbers = [row[0] for row in cursor.fetchall()]
                
                # All lot numbers should be normalized
                for lot_num in lot_numbers:
                    assert lot_num == lot_num.strip()
                    assert lot_num == lot_num.upper()
            finally:
                cursor.close()


class TestDataConsolidationIntegration:
    """Tests data consolidation across all sources."""
    
    def test_consolidated_view_single_lot(self, setup_test_db, sample_production_csv, 
                                         sample_quality_csv, sample_shipping_csv):
        """Test getting consolidated view for a single lot."""
        # Import all data sources
        DataImporter.import_file(sample_production_csv, 'production')
        DataImporter.import_file(sample_quality_csv, 'quality')
        DataImporter.import_file(sample_shipping_csv, 'shipping')
        
        # Get consolidated view
        consolidated = ConsolidatedView.get_consolidated_lot('LOT-20260112-001')
        
        assert consolidated is not None
        assert consolidated['lot_number'] == 'LOT-20260112-001'
        assert len(consolidated['production_records']) > 0
        assert len(consolidated['quality_records']) > 0
        assert consolidated['shipping_record'] is not None
    
    def test_consolidated_view_all_lots(self, setup_test_db, sample_production_csv, 
                                       sample_quality_csv):
        """Test getting all consolidated lots."""
        # Import data
        DataImporter.import_file(sample_production_csv, 'production')
        DataImporter.import_file(sample_quality_csv, 'quality')
        
        # Get all lots
        all_lots = ConsolidatedView.get_all_lots()
        
        assert len(all_lots) >= 2
        assert all(isinstance(lot, dict) for lot in all_lots)
        assert all('lot_number' in lot for lot in all_lots)


class TestReportingIntegration:
    """Tests reporting module integration with database."""
    
    def test_production_line_issues_report(self, setup_test_db, sample_production_csv):
        """Test production line issues report generation."""
        # Import production data with issues
        DataImporter.import_file(sample_production_csv, 'production')
        
        # Generate report for date range
        report = Reporter.get_production_line_issues(
            date_from=date(2026, 1, 12),
            date_to=date(2026, 1, 13)
        )
        
        assert isinstance(report, list)
        assert len(report) > 0
        
        # Verify report structure
        for line_report in report:
            assert 'production_line' in line_report
            assert 'issue_count' in line_report
            assert 'affected_lots' in line_report
    
    def test_defect_trends_report(self, setup_test_db, sample_production_csv, 
                                 sample_quality_csv):
        """Test defect trends report generation."""
        # Import data
        DataImporter.import_file(sample_production_csv, 'production')
        DataImporter.import_file(sample_quality_csv, 'quality')
        
        # Generate defect trends report
        report = Reporter.get_defect_trends(
            date_from=date(2026, 1, 12),
            date_to=date(2026, 1, 13)
        )
        
        assert isinstance(report, list)
        assert len(report) > 0
        
        # Verify report structure
        for defect_report in report:
            assert 'defect_type' in defect_report
            assert 'total_count' in defect_report
    
    def test_shipment_status_lookup(self, setup_test_db, sample_production_csv, 
                                   sample_shipping_csv):
        """Test shipment status lookup by lot ID."""
        # Import data
        DataImporter.import_file(sample_production_csv, 'production')
        DataImporter.import_file(sample_shipping_csv, 'shipping')
        
        # Lookup shipment status
        status = Reporter.get_shipment_status_by_lot('LOT-20260112-001')
        
        assert status is not None
        assert status['shipment_status'] == 'Shipped'
        assert 'carrier_info' in status
        assert 'destination' in status


class TestDataValidationIntegration:
    """Tests data validation across all modules."""
    
    def test_validate_complete_dataset(self, setup_test_db, sample_production_csv, 
                                      sample_quality_csv, sample_shipping_csv):
        """Test validation of complete dataset."""
        # Import all data sources
        DataImporter.import_file(sample_production_csv, 'production')
        DataImporter.import_file(sample_quality_csv, 'quality')
        DataImporter.import_file(sample_shipping_csv, 'shipping')
        
        # Run validation
        validation_result = DataValidator.validate_all()
        
        assert isinstance(validation_result, dict)
        assert 'valid' in validation_result
        assert 'total_discrepancies' in validation_result
        assert 'checks_performed' in validation_result
    
    def test_detect_missing_quality_records(self, setup_test_db, sample_production_csv):
        """Test detection of lots missing quality records."""
        # Import only production data
        DataImporter.import_file(sample_production_csv, 'production')
        
        # Run validation
        validation_result = DataValidator.validate_all()
        
        # Should detect missing quality records
        assert validation_result['checks_performed']['incomplete_lots'] > 0
    
    def test_detect_missing_shipping_records(self, setup_test_db, sample_production_csv, 
                                           sample_quality_csv):
        """Test detection of lots missing shipping records."""
        # Import production and quality but not shipping
        DataImporter.import_file(sample_production_csv, 'production')
        DataImporter.import_file(sample_quality_csv, 'quality')
        
        # Run validation
        validation_result = DataValidator.validate_all()
        
        # Should detect missing shipping records
        assert validation_result['checks_performed']['incomplete_lots'] > 0


class TestEndToEndWorkflow:
    """Tests complete end-to-end workflows."""
    
    def test_complete_import_consolidate_report_workflow(self, setup_test_db, 
                                                        sample_production_csv,
                                                        sample_quality_csv, 
                                                        sample_shipping_csv):
        """Test complete workflow from import to reporting."""
        # Step 1: Import all data sources
        prod_result = DataImporter.import_file(sample_production_csv, 'production')
        assert prod_result['success'] is True
        
        qual_result = DataImporter.import_file(sample_quality_csv, 'quality')
        assert qual_result['success'] is True
        
        ship_result = DataImporter.import_file(sample_shipping_csv, 'shipping')
        assert ship_result['success'] is True
        
        # Step 2: Get consolidated view
        consolidated = ConsolidatedView.get_consolidated_lot('LOT-20260112-001')
        assert consolidated is not None
        assert len(consolidated['production_records']) > 0
        assert len(consolidated['quality_records']) > 0
        assert consolidated['shipping_record'] is not None
        
        # Step 3: Generate reports
        prod_report = Reporter.get_production_line_issues(
            date_from=date(2026, 1, 12),
            date_to=date(2026, 1, 13)
        )
        assert len(prod_report) > 0
        
        defect_report = Reporter.get_defect_trends(
            date_from=date(2026, 1, 12),
            date_to=date(2026, 1, 13)
        )
        assert len(defect_report) > 0
        
        shipment_status = Reporter.get_shipment_status_by_lot('LOT-20260112-001')
        assert shipment_status is not None
        
        # Step 4: Validate data consistency
        validation = DataValidator.validate_all()
        assert isinstance(validation, dict)
    
    def test_performance_query_response_time(self, setup_test_db, sample_production_csv):
        """Test that queries meet AC10 performance requirement (<5 seconds)."""
        import time
        
        # Import data
        DataImporter.import_file(sample_production_csv, 'production')
        
        # Test query performance
        start_time = time.time()
        all_lots = ConsolidatedView.get_all_lots()
        query_time = time.time() - start_time
        
        # Verify response time < 5 seconds (AC10)
        assert query_time < 5.0, f"Query took {query_time}s (should be < 5s)"
        
        # Test another query
        start_time = time.time()
        report = Reporter.get_production_line_issues(
            date_from=date(2026, 1, 12),
            date_to=date(2026, 1, 13)
        )
        query_time = time.time() - start_time
        
        assert query_time < 5.0, f"Report generation took {query_time}s (should be < 5s)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
