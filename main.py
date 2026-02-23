"""
Operations Data Consolidation - Main Application
================================================

Main entry point for the Operations Data Consolidation application.

This application consolidates production, quality, and shipping data
to help operations analysts quickly answer summary questions about
issues, defects, and shipment status.

Features:
- Multi-source data import (CSV, Excel) - AC1
- Unified data consolidation - AC2
- Lot ID normalization - AC3
- Production line issue reporting - AC4
- Defect trend analysis - AC5
- Shipment status tracking - AC6
- Automatic report generation - AC9
- Data consistency validation - AC8
- Fast query response times - AC10

Time Complexity: Query/report operations are O(n) where n = record count
Space Complexity: Memory usage is O(m) where m = batch size
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

from config import Config
from database import Database
from data_importer import DataImporter
from data_normalizer import LotIDNormalizer
from data_consolidator import ConsolidatedView
from reporter import Reporter
from data_validator import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OperationsConsolidationApp:
    """
    Main application class for Operations Data Consolidation.
    
    Orchestrates all modules and provides a unified interface for:
    - Data import
    - Data consolidation
    - Reporting and analysis
    - Data validation
    
    This class manages the application lifecycle and ensures proper
    resource cleanup.
    """
    
    def __init__(self):
        """
        Initializes the application.
        
        Time Complexity: O(1) for initialization
        Space Complexity: O(n) where n = connection pool size
        """
        self.initialized = False
    
    def initialize(self):
        """
        Initializes the database and validates configuration.
        
        Time Complexity: O(m) where m = schema statement count
        Space Complexity: O(n) for connection pool
        
        Returns:
            bool: True if initialization successful
        
        Raises:
            Exception: If configuration or database init fails
        """
        try:
            logger.info("=" * 60)
            logger.info("Operations Data Consolidation Application")
            logger.info("=" * 60)
            
            # Validate configuration
            logger.info("Validating configuration...")
            is_valid, error = Config.validate_configuration()
            if not is_valid:
                logger.error(f"Configuration error: {error}")
                return False
            
            # Initialize database
            logger.info("Initializing database...")
            Database.initialize()
            
            self.initialized = True
            logger.info("✓ Application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
    
    def import_data(self, file_path, source_type):
        """
        Imports data from a file (CSV or Excel).
        
        Implements AC1 - Multi-Source Import.
        
        Time Complexity: O(n) where n = number of rows in file
        Space Complexity: O(b) where b = batch size
        
        Args:
            file_path (str): Path to file to import
            source_type (str): Type of source ('production', 'quality', 'shipping')
        
        Returns:
            dict: Import result with success status and row counts
        """
        if not self.initialized:
            logger.error("Application not initialized")
            return {'success': False}
        
        logger.info(f"Importing {source_type} data from {file_path}")
        result = DataImporter.import_file(file_path, source_type)
        
        if result['success']:
            logger.info(f"✓ Import successful: {result['rows_imported']} rows imported")
        else:
            logger.error(f"✗ Import failed: {result['errors']}")
        
        return result
    
    def get_consolidated_lot(self, lot_identifier):
        """
        Retrieves consolidated view of a single lot.
        
        Implements AC2 - Unified Data View.
        
        Time Complexity: O(n) where n = records for this lot
        Space Complexity: O(n)
        
        Args:
            lot_identifier (str or int): Lot ID or lot number
        
        Returns:
            dict: Consolidated lot data or None
        """
        logger.info(f"Retrieving consolidated data for lot: {lot_identifier}")
        
        consolidated = ConsolidatedView.get_consolidated_lot(lot_identifier)
        
        if consolidated:
            logger.info(f"✓ Found lot {consolidated['lot_number']}")
            return consolidated
        else:
            logger.warning(f"✗ No lot found for identifier: {lot_identifier}")
            return None
    
    def get_production_line_issues(self, date_from, date_to=None):
        """
        Gets production line issue summary (AC4).
        
        AC4 - Production Line Issues:
        - Display summary of issues by production line
        - Allow filtering by date range (weekly view)
        
        Time Complexity: O(n log n) where n = production records
        Space Complexity: O(m) where m = distinct lines
        
        Args:
            date_from (date): Start of date range
            date_to (date): End of date range (defaults to date_from)
        
        Returns:
            list: Production line issue summaries
        """
        logger.info(f"Getting production line issues for {date_from} to {date_to or date_from}")
        
        issues = Reporter.get_production_line_issues(date_from, date_to)
        logger.info(f"✓ Found issue summary for {len(issues)} production lines")
        
        return issues
    
    def get_defect_trends(self, days_back=30, groupby='day'):
        """
        Gets defect trends over time (AC5).
        
        AC5 - Defect Type Trends:
        - Show defect counts grouped by defect type
        - Support trend visualization over time
        
        Time Complexity: O(n log n) where n = quality records
        Space Complexity: O(n)
        
        Args:
            days_back (int): Number of days to look back
            groupby (str): Grouping granularity ('day', 'week', 'month')
        
        Returns:
            list: Defect trends with date and count
        """
        logger.info(f"Getting defect trends for past {days_back} days")
        
        trends = Reporter.get_defect_trends(days_back, groupby)
        logger.info(f"✓ Found {len(trends)} trend data points")
        
        return trends
    
    def get_shipment_status(self, lot_identifier):
        """
        Gets shipment status for a lot (AC6).
        
        AC6 - Batch Shipment Status:
        - Search by lot ID
        - Display shipment status (Shipped, Pending, Not Shipped)
        
        Time Complexity: O(1) for index lookup
        Space Complexity: O(1)
        
        Args:
            lot_identifier (str or int): Lot ID or lot number
        
        Returns:
            dict: Shipment status or None
        """
        logger.info(f"Getting shipment status for lot: {lot_identifier}")
        
        status = Reporter.get_shipment_status(lot_number=lot_identifier)
        
        if status:
            logger.info(f"✓ Shipment status: {status['shipment_status']}")
        else:
            logger.warning(f"✗ No shipment record found")
        
        return status
    
    def validate_data(self):
        """
        Validates data consistency across all sources (AC8).
        
        AC8 - Data Consistency Checks:
        - Identify discrepancies across data sources
        - Flag unmatched or ambiguous lot IDs
        - Provide clear indication of missing records
        
        Time Complexity: O(n) where n = total records
        Space Complexity: O(d) where d = discrepancies found
        
        Returns:
            dict: Validation results with discrepancy counts
        """
        logger.info("Starting data consistency validation...")
        
        results = DataValidator.validate_all()
        
        logger.info(f"✓ Validation complete: {results['total_discrepancies']} discrepancies found")
        
        if not results['valid']:
            discrepancies = DataValidator.get_discrepancies(limit=10)
            for disc in discrepancies:
                logger.warning(f"  - Lot {disc['lot_id']}: {disc['description']}")
        
        return results
    
    def export_report(self, report_type, output_format='json', **kwargs):
        """
        Exports a report to file.
        
        Implements AC9 - Report Generation:
        - Export summary reports (JSON, CSV)
        - Include production line issues
        - Include defect trends
        - Include shipment status
        
        Time Complexity: O(n) where n = report data size
        Space Complexity: O(n)
        
        Args:
            report_type (str): Type of report
                ('production_issues', 'defect_trends', 'shipment_status')
            output_format (str): Output format ('json', 'csv')
            **kwargs: Report-specific parameters
        
        Returns:
            str: Report content or None if failed
        """
        logger.info(f"Generating {report_type} report ({output_format})")
        
        if report_type == 'production_issues':
            date_from = kwargs.get('date_from', date.today() - timedelta(days=7))
            date_to = kwargs.get('date_to', date.today())
            report = Reporter.export_production_line_report(date_from, date_to, output_format)
        
        elif report_type == 'defect_trends':
            days_back = kwargs.get('days_back', 30)
            report = Reporter.export_defect_trends_report(days_back, output_format)
        
        elif report_type == 'shipment_status':
            report = Reporter.export_shipment_status_report(output_format)
        
        else:
            logger.error(f"Unknown report type: {report_type}")
            return None
        
        if report:
            logger.info(f"✓ Report generated successfully")
        else:
            logger.error(f"✗ Report generation failed")
        
        return report
    
    def check_performance(self):
        """
        Validates performance meets AC10 requirements.
        
        AC10 - Response Time:
        - Generate summary results within 5 seconds for standard dataset
        
        Time Complexity: Varies by query (should all be < 5 seconds)
        Space Complexity: O(n)
        
        Returns:
            dict: Performance test results
        """
        logger.info("Checking performance against AC10 requirements...")
        
        results = DataValidator.validate_performance()
        
        for test_name, test_result in results['tests'].items():
            status = "✓ PASS" if test_result['pass'] else "✗ FAIL"
            logger.info(f"  {status}: {test_name} - {test_result['time_seconds']}s "
                       f"(timeout: {results['timeout_seconds']}s)")
        
        if results['all_pass']:
            logger.info("✓ All performance tests passed")
        else:
            logger.warning("✗ Some performance tests failed")
        
        return results
    
    def shutdown(self):
        """
        Cleanly shuts down the application.
        
        Time Complexity: O(n) where n = active connections
        Space Complexity: O(1)
        """
        logger.info("Shutting down application...")
        Database.close_all()
        logger.info("✓ Application shutdown complete")


# ===== Command-line Interface =====

def print_menu():
    """Prints the main menu options."""
    print("\n" + "=" * 60)
    print("Operations Data Consolidation System")
    print("=" * 60)
    print("1. Import Data (CSV/Excel)")
    print("2. View Consolidated Lot")
    print("3. Production Line Issues Report")
    print("4. Defect Trends Analysis")
    print("5. Shipment Status Lookup")
    print("6. Validate Data Consistency")
    print("7. Export Report")
    print("8. Check Performance")
    print("9. Exit")
    print("-" * 60)


def main():
    """
    Main application entry point.
    
    Provides interactive CLI for using the application.
    """
    app = OperationsConsolidationApp()
    
    # Initialize application
    if not app.initialize():
        logger.error("Failed to initialize application")
        return 1
    
    try:
        while True:
            print_menu()
            choice = input("Enter choice (1-9): ").strip()
            
            if choice == '1':
                # Import data
                file_path = input("Enter file path: ").strip()
                print("Source type options: production, quality, shipping")
                source_type = input("Enter source type: ").strip().lower()
                
                result = app.import_data(file_path, source_type)
                print(f"Import result: {result}")
            
            elif choice == '2':
                # View consolidated lot
                lot_id = input("Enter lot ID or lot number: ").strip()
                lot_data = app.get_consolidated_lot(lot_id)
                if lot_data:
                    print(f"\nLot: {lot_data['lot_number']}")
                    print(f"Production Date: {lot_data['production_date']}")
                    print(f"Production Line: {lot_data['production_line']}")
                    print(f"Summary: {lot_data['summary']}")
            
            elif choice == '3':
                # Production line issues
                date_from = input("Enter start date (YYYY-MM-DD): ").strip()
                date_to = input("Enter end date (YYYY-MM-DD) [optional]: ").strip() or None
                
                issues = app.get_production_line_issues(
                    datetime.strptime(date_from, '%Y-%m-%d').date(),
                    datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
                )
                
                for issue in issues:
                    print(f"{issue['production_line']}: {issue['issue_count']} issues")
            
            elif choice == '4':
                # Defect trends
                days = int(input("Enter number of days to analyze (default 30): ") or "30")
                trends = app.get_defect_trends(days)
                print(f"Found {len(trends)} trend data points")
            
            elif choice == '5':
                # Shipment status
                lot_id = input("Enter lot ID or number: ").strip()
                status = app.get_shipment_status(lot_id)
                if status:
                    print(f"Status: {status['shipment_status']}")
            
            elif choice == '6':
                # Data validation
                results = app.validate_data()
                print(f"Validation results: {results}")
            
            elif choice == '7':
                # Export report
                print("Report types: production_issues, defect_trends, shipment_status")
                report_type = input("Enter report type: ").strip()
                report = app.export_report(report_type, 'json')
                if report:
                    print(f"Report:\n{report[:500]}...")
            
            elif choice == '8':
                # Performance check
                results = app.check_performance()
                print(f"Performance results: {results}")
            
            elif choice == '9':
                print("Exiting...")
                break
            
            else:
                print("Invalid choice. Please try again.")
    
    finally:
        app.shutdown()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
