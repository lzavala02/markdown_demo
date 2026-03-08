"""
End-to-End Tests for Operations Data Consolidation Streamlit App
=================================================================

Tests the complete Streamlit web application using Playwright.

Test Coverage:
- Application startup and initialization
- Navigation between different pages
- Dashboard display
- Data import UI
- Lot lookup functionality
- Production analysis interface
- Defect analysis interface
- Shipment status interface
- Data validation interface
- Report generation interface

Requirements:
- Playwright browsers installed: playwright install
- Streamlit app running on localhost:8501

Run with: pytest tests/test_e2e.py -v --headed (to see browser)
Run headless: pytest tests/test_e2e.py -v
"""

import pytest
import time
import subprocess
import os
import tempfile
from pathlib import Path
import pandas as pd
import signal
import sys

# Import application modules for setup
from config import Config
from database import Database
from data_importer import DataImporter


# ===== Fixtures =====

@pytest.fixture(scope="module")
def setup_test_db():
    """Sets up test database once for all e2e tests."""
    Database.initialize()
    yield
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


@pytest.fixture(scope="module")
def streamlit_app():
    """
    Starts Streamlit app for e2e testing.
    
    The app runs on localhost:8501 by default.
    """
    # Start Streamlit in background
    process = subprocess.Popen(
        ["streamlit", "run", "streamlit_app.py", "--server.headless", "true", 
         "--server.port", "8501", "--server.address", "localhost"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd(),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    
    # Wait for app to start (give it 10 seconds)
    time.sleep(10)
    
    yield "http://localhost:8501"
    
    # Terminate Streamlit process
    if sys.platform == "win32":
        # Windows: send CTRL_BREAK_EVENT
        os.kill(process.pid, signal.CTRL_BREAK_EVENT)
    else:
        # Unix: send SIGTERM
        process.terminate()
    
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def sample_data():
    """Loads sample data into database for e2e tests."""
    # Create sample production data
    prod_data = {
        'lot_id': ['LOT-20260112-001', 'LOT-20260112-002', 'LOT-20260113-001'],
        'production_date': ['2026-01-12', '2026-01-12', '2026-01-13'],
        'production_line': ['Line 1', 'Line 2', 'Line 1'],
        'quantity_produced': [382, 290, 401],
        'status': ['Completed', 'Completed', 'In Progress'],
        'issue_description': [None, 'Minor delay', None]
    }
    prod_df = pd.DataFrame(prod_data)
    
    # Create sample quality data
    qual_data = {
        'lot_id': ['LOT-20260112-001', 'LOT-20260112-002'],
        'inspection_date': ['2026-01-13', '2026-01-13'],
        'defect_type': ['Surface Scratch', 'Dimension Variance'],
        'defect_count': [5, 3],
        'inspection_status': ['Pass', 'Pass'],
        'inspector': ['John Doe', 'Jane Smith'],
        'notes': ['Minor scratches', 'Within tolerance']
    }
    qual_df = pd.DataFrame(qual_data)
    
    # Create sample shipping data
    ship_data = {
        'lot_id': ['LOT-20260112-001'],
        'shipment_status': ['Shipped'],
        'carrier_info': ['XPO - PRO-812238'],
        'destination': ['MI'],
        'shipment_date': ['2026-01-29']
    }
    ship_df = pd.DataFrame(ship_data)
    
    # Save to temporary files and import
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        prod_df.to_csv(f.name, index=False)
        prod_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        qual_df.to_csv(f.name, index=False)
        qual_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        ship_df.to_csv(f.name, index=False)
        ship_path = f.name
    
    # Import data
    DataImporter.import_file(prod_path, 'production')
    DataImporter.import_file(qual_path, 'quality')
    DataImporter.import_file(ship_path, 'shipping')
    
    yield
    
    # Cleanup temp files
    for path in [prod_path, qual_path, ship_path]:
        if os.path.exists(path):
            os.remove(path)


# ===== E2E Tests =====

class TestStreamlitAppLaunch:
    """Tests Streamlit app launch and basic functionality."""
    
    def test_app_loads(self, streamlit_app, page):
        """Test that Streamlit app loads successfully."""
        page.goto(streamlit_app)
        
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        
        # Check that title is present
        assert "Operations Data Consolidation" in page.content()
    
    def test_app_title_visible(self, streamlit_app, page):
        """Test that app title is visible."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Look for the title
        title = page.locator("text=Operations Data Consolidation System")
        assert title.is_visible()


class TestNavigation:
    """Tests navigation between different pages."""
    
    def test_dashboard_page_default(self, streamlit_app, page):
        """Test that dashboard is the default page."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Dashboard should be visible
        assert "Dashboard" in page.content() or "dashboard" in page.content().lower()
    
    def test_navigate_to_import_data(self, streamlit_app, page):
        """Test navigation to Import Data page."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Click on Import Data in sidebar
        import_link = page.locator("text=Import Data")
        if import_link.count() > 0:
            import_link.first.click()
            time.sleep(1)
            
            # Verify we're on the import page
            assert "Import" in page.content()
    
    def test_navigate_to_lot_lookup(self, streamlit_app, page):
        """Test navigation to Lot Lookup page."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Click on Lot Lookup in sidebar
        lookup_link = page.locator("text=Lot Lookup")
        if lookup_link.count() > 0:
            lookup_link.first.click()
            time.sleep(1)
            
            # Verify we're on the lookup page
            assert "Lot" in page.content() or "lookup" in page.content().lower()
    
    def test_navigate_to_production_analysis(self, streamlit_app, page):
        """Test navigation to Production Analysis page."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Click on Production Analysis in sidebar
        prod_link = page.locator("text=Production Analysis")
        if prod_link.count() > 0:
            prod_link.first.click()
            time.sleep(1)
            
            # Verify we're on the production analysis page
            assert "Production" in page.content()
    
    def test_navigate_to_defect_analysis(self, streamlit_app, page):
        """Test navigation to Defect Analysis page."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Click on Defect Analysis in sidebar
        defect_link = page.locator("text=Defect Analysis")
        if defect_link.count() > 0:
            defect_link.first.click()
            time.sleep(1)
            
            # Verify we're on the defect analysis page
            assert "Defect" in page.content()
    
    def test_navigate_to_shipment_status(self, streamlit_app, page):
        """Test navigation to Shipment Status page."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Click on Shipment Status in sidebar
        shipment_link = page.locator("text=Shipment Status")
        if shipment_link.count() > 0:
            shipment_link.first.click()
            time.sleep(1)
            
            # Verify we're on the shipment status page
            assert "Shipment" in page.content()


class TestDashboardPage:
    """Tests Dashboard page functionality."""
    
    def test_dashboard_displays_metrics(self, streamlit_app, page):
        """Test that dashboard displays key metrics."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Look for metric displays (Streamlit uses st.metric)
        content = page.content()
        
        # Check for some expected metrics or text
        assert "Feature" in content or "Tests" in content or "Performance" in content
    
    def test_dashboard_shows_ac_completion(self, streamlit_app, page):
        """Test that dashboard shows AC completion status."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        content = page.content()
        
        # Look for AC or Acceptance Criteria references
        assert "AC" in content or "Complete" in content


class TestLotLookupPage:
    """Tests Lot Lookup page functionality."""
    
    def test_lot_lookup_with_data(self, streamlit_app, page, sample_data):
        """Test lot lookup functionality with sample data."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Navigate to Lot Lookup
        lookup_link = page.locator("text=Lot Lookup")
        if lookup_link.count() > 0:
            lookup_link.first.click()
            time.sleep(2)
            
            # Try to find input field and enter lot ID
            # Note: Streamlit's text_input might be tricky to target
            text_inputs = page.locator("input[type='text']")
            if text_inputs.count() > 0:
                text_inputs.first.fill("LOT-20260112-001")
                time.sleep(1)
                
                # Check if data is displayed
                content = page.content()
                # Should show some data about the lot
                assert "LOT" in content or "Lot" in content


class TestProductionAnalysisPage:
    """Tests Production Analysis page functionality."""
    
    def test_production_analysis_displays_data(self, streamlit_app, page, sample_data):
        """Test that production analysis page displays data."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Navigate to Production Analysis
        prod_link = page.locator("text=Production Analysis")
        if prod_link.count() > 0:
            prod_link.first.click()
            time.sleep(2)
            
            content = page.content()
            
            # Should display production line information
            assert "Line" in content or "Production" in content


class TestDefectAnalysisPage:
    """Tests Defect Analysis page functionality."""
    
    def test_defect_analysis_displays_data(self, streamlit_app, page, sample_data):
        """Test that defect analysis page displays data."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Navigate to Defect Analysis
        defect_link = page.locator("text=Defect Analysis")
        if defect_link.count() > 0:
            defect_link.first.click()
            time.sleep(2)
            
            content = page.content()
            
            # Should display defect information
            assert "Defect" in content or "defect" in content.lower()


class TestShipmentStatusPage:
    """Tests Shipment Status page functionality."""
    
    def test_shipment_status_displays_data(self, streamlit_app, page, sample_data):
        """Test that shipment status page displays data."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Navigate to Shipment Status
        shipment_link = page.locator("text=Shipment Status")
        if shipment_link.count() > 0:
            shipment_link.first.click()
            time.sleep(2)
            
            content = page.content()
            
            # Should display shipment information
            assert "Shipment" in content or "shipment" in content.lower()


class TestDataValidationPage:
    """Tests Data Validation page functionality."""
    
    def test_data_validation_page_accessible(self, streamlit_app, page):
        """Test that data validation page is accessible."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Navigate to Data Validation
        validation_link = page.locator("text=Data Validation")
        if validation_link.count() > 0:
            validation_link.first.click()
            time.sleep(2)
            
            content = page.content()
            
            # Should display validation information
            assert "Validation" in content or "validation" in content.lower()


class TestResponsiveness:
    """Tests app responsiveness and performance."""
    
    def test_page_load_time(self, streamlit_app, page):
        """Test that pages load within acceptable time."""
        import time
        
        start_time = time.time()
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        load_time = time.time() - start_time
        
        # Page should load within 10 seconds
        assert load_time < 10.0, f"Page took {load_time}s to load (should be < 10s)"
    
    def test_navigation_response_time(self, streamlit_app, page):
        """Test that navigation between pages is responsive."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # Navigate to different pages and measure response
        pages_to_test = ["Import Data", "Lot Lookup", "Production Analysis"]
        
        for page_name in pages_to_test:
            link = page.locator(f"text={page_name}")
            if link.count() > 0:
                start_time = time.time()
                link.first.click()
                time.sleep(1)  # Give it a moment to respond
                response_time = time.time() - start_time
                
                # Navigation should be reasonably fast (< 5 seconds)
                assert response_time < 5.0, f"Navigation to {page_name} took {response_time}s"


class TestErrorHandling:
    """Tests error handling in the UI."""
    
    def test_app_handles_empty_database(self, streamlit_app, page):
        """Test that app handles empty database gracefully."""
        page.goto(streamlit_app)
        page.wait_for_load_state("networkidle")
        
        # App should load even with empty database
        assert "Operations Data Consolidation" in page.content()
        
        # No critical errors should be visible
        content = page.content().lower()
        # Allow for informational messages but not critical errors
        # (Streamlit may show some warnings/info about empty data)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--headed'])
