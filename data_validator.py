"""
Data Validator Module
=====================
Validates data consistency and integrity across sources (AC8, AC10).

Implements:
- AC8: Data Consistency Checks
  - Identify discrepancies across data sources
  - Flag missing or inconsistent records
  - Track unmatched Lot IDs
  
- AC10: Performance checks for response time < 5 seconds

Time Complexity: O(n) for validation passes where n = record count
Space Complexity: O(n) for discrepancy tracking
"""

import logging
from datetime import datetime
from database import Database
from data_normalizer import LotIDNormalizer
from psycopg2 import Error
from config import Config

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates data consistency and quality across data sources.
    
    Checks include:
    1. Orphaned records (exist in one source but not another)
    2. Missing required fields
    3. Invalid data types
    4. Unmatched Lot IDs
    5. Performance thresholds (AC10)
    
    All findings are recorded in data_discrepancies table for review.
    """
    
    # ===== AC8: Data Consistency Checks =====
    
    @staticmethod
    def validate_all():
        """
        Runs complete data consistency validation.
        
        Executes all validation checks and records findings.
        
        Time Complexity: O(n) where n = total records across all tables
        Space Complexity: O(d) where d = discrepancies found
        
        Returns:
            dict: Validation results
            {
                'valid': bool,
                'total_discrepancies': int,
                'orphaned_production': int,
                'orphaned_quality': int,
                'orphaned_shipping': int,
                'unmatched_lot_ids': int,
                'timestamp': datetime
            }
        """
        results = {
            'valid': True,
            'total_discrepancies': 0,
            'checks_performed': {},
            'timestamp': datetime.now()
        }
        
        try:
            # Check 1: Production records with missing lots
            orphaned_prod = DataValidator._find_orphaned_production()
            results['checks_performed']['orphaned_production'] = len(orphaned_prod)
            results['total_discrepancies'] += len(orphaned_prod)
            
            # Check 2: Quality records with missing lots
            orphaned_quality = DataValidator._find_orphaned_quality()
            results['checks_performed']['orphaned_quality'] = len(orphaned_quality)
            results['total_discrepancies'] += len(orphaned_quality)
            
            # Check 3: Shipping records with missing lots
            orphaned_shipping = DataValidator._find_orphaned_shipping()
            results['checks_performed']['orphaned_shipping'] = len(orphaned_shipping)
            results['total_discrepancies'] += len(orphaned_shipping)
            
            # Check 4: Unmatched Lot IDs
            unmatched = DataValidator._find_unmatched_lot_ids()
            results['checks_performed']['unmatched_lot_ids'] = len(unmatched)
            results['total_discrepancies'] += len(unmatched)
            
            # Check 5: Lots missing from any source
            incomplete = DataValidator._find_incomplete_lots()
            results['checks_performed']['incomplete_lots'] = len(incomplete)
            results['total_discrepancies'] += len(incomplete)
            
            results['valid'] = results['total_discrepancies'] == 0
            
            logger.info(f"Validation complete: {results['total_discrepancies']} discrepancies found")
            
        except Error as e:
            logger.error(f"Validation error: {e}")
            results['valid'] = False
            results['error'] = str(e)
        
        return results
    
    @staticmethod
    def _find_orphaned_production():
        """
        Finds production records without matching lot records.
        
        AC8 - Identifies lot exists in production but not in lot master.
        
        Time Complexity: O(n)
        Space Complexity: O(m) where m = orphaned record count
        
        Returns:
            list: List of orphaned production records
        """
        try:
            query = """
            SELECT pr.production_record_id, pr.lot_id
            FROM production_records pr
            WHERE NOT EXISTS (SELECT 1 FROM lots l WHERE l.lot_id = pr.lot_id)
            """
            
            results = Database.execute_query(query, None)
            
            for record_id, lot_id in results:
                DataValidator._record_discrepancy(
                    lot_id=lot_id,
                    missing_in_source='lots',
                    description=f'Production record {record_id} references non-existent lot'
                )
            
            return results
            
        except Error as e:
            logger.error(f"Error finding orphaned production: {e}")
            return []
    
    @staticmethod
    def _find_orphaned_quality():
        """
        Finds quality records without matching lot records.
        
        AC8 - Identifies lot exists in quality but not in lot master.
        
        Time Complexity: O(n)
        Space Complexity: O(m)
        
        Returns:
            list: List of orphaned quality records
        """
        try:
            query = """
            SELECT qr.quality_record_id, qr.lot_id
            FROM quality_records qr
            WHERE NOT EXISTS (SELECT 1 FROM lots l WHERE l.lot_id = qr.lot_id)
            """
            
            results = Database.execute_query(query, None)
            
            for record_id, lot_id in results:
                DataValidator._record_discrepancy(
                    lot_id=lot_id,
                    missing_in_source='lots',
                    description=f'Quality record {record_id} references non-existent lot'
                )
            
            return results
            
        except Error as e:
            logger.error(f"Error finding orphaned quality: {e}")
            return []
    
    @staticmethod
    def _find_orphaned_shipping():
        """
        Finds shipping records without matching lot records.
        
        AC8 - Identifies lot exists in shipping but not in lot master.
        
        Time Complexity: O(n)
        Space Complexity: O(m)
        
        Returns:
            list: List of orphaned shipping records
        """
        try:
            query = """
            SELECT sr.shipping_record_id, sr.lot_id
            FROM shipping_records sr
            WHERE NOT EXISTS (SELECT 1 FROM lots l WHERE l.lot_id = sr.lot_id)
            """
            
            results = Database.execute_query(query, None)
            
            for record_id, lot_id in results:
                DataValidator._record_discrepancy(
                    lot_id=lot_id,
                    missing_in_source='lots',
                    description=f'Shipping record {record_id} references non-existent lot'
                )
            
            return results
            
        except Error as e:
            logger.error(f"Error finding orphaned shipping: {e}")
            return []
    
    @staticmethod
    def _find_unmatched_lot_ids():
        """
        Finds Lot IDs that could not be normalized/matched.
        
        AC8 - Flags problematic Lot IDs for manual review.
        
        Time Complexity: O(n)
        Space Complexity: O(m)
        
        Returns:
            list: List of unmatched Lot IDs
        """
        try:
            query = """
            SELECT lot_id_normalization_id, original_lot_number, normalized_lot_number, validation_status
            FROM lot_id_normalizations
            WHERE validation_status IN ('Ambiguous', 'Unmatched')
            """
            
            results = Database.execute_query(query, None)
            return results
            
        except Error as e:
            logger.error(f"Error finding unmatched lot IDs: {e}")
            return []
    
    @staticmethod
    def _find_incomplete_lots():
        """
        Finds lots missing records from any source.
        
        AC8 - Flags lots that appear in some sources but not others.
        
        Identifies:
        - Lots without production records
        - Lots without quality records
        - Lots without shipping records
        
        Time Complexity: O(n)
        Space Complexity: O(m)
        
        Returns:
            list: List of incomplete lots (missing data from sources)
        """
        try:
            incomplete_lots = []
            
            # Lots without production records
            query1 = """
            SELECT l.lot_id FROM lots l
            WHERE NOT EXISTS (SELECT 1 FROM production_records pr WHERE pr.lot_id = l.lot_id)
            """
            results1 = Database.execute_query(query1, None)
            for (lot_id,) in results1:
                DataValidator._record_discrepancy(
                    lot_id=lot_id,
                    missing_in_source='production',
                    description='Lot has no production records'
                )
                incomplete_lots.append(lot_id)
            
            # Lots without quality records
            query2 = """
            SELECT l.lot_id FROM lots l
            WHERE NOT EXISTS (SELECT 1 FROM quality_records qr WHERE qr.lot_id = l.lot_id)
            """
            results2 = Database.execute_query(query2, None)
            for (lot_id,) in results2:
                DataValidator._record_discrepancy(
                    lot_id=lot_id,
                    missing_in_source='quality',
                    description='Lot has no quality inspection records'
                )
                if lot_id not in incomplete_lots:
                    incomplete_lots.append(lot_id)
            
            # Lots without shipping records
            query3 = """
            SELECT l.lot_id FROM lots l
            WHERE NOT EXISTS (SELECT 1 FROM shipping_records sr WHERE sr.lot_id = l.lot_id)
            """
            results3 = Database.execute_query(query3, None)
            for (lot_id,) in results3:
                DataValidator._record_discrepancy(
                    lot_id=lot_id,
                    missing_in_source='shipping',
                    description='Lot has no shipping record'
                )
                if lot_id not in incomplete_lots:
                    incomplete_lots.append(lot_id)
            
            return incomplete_lots
            
        except Error as e:
            logger.error(f"Error finding incomplete lots: {e}")
            return []
    
    @staticmethod
    def _record_discrepancy(lot_id, missing_in_source, description):
        """
        Records a data discrepancy in the database.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Args:
            lot_id (int): Affected lot ID
            missing_in_source (str): Which source is missing data
            description (str): Description of discrepancy
        """
        try:
            insert_sql = """
            INSERT INTO data_discrepancies (lot_id, missing_in_source, description)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            """
            
            Database.execute_update(insert_sql, (lot_id, missing_in_source, description))
            
        except Error as e:
            logger.warning(f"Failed to record discrepancy: {e}")
    
    # ===== AC10: Performance Validation =====
    
    @staticmethod
    def validate_performance():
        """
        Validates that response times meet AC10 requirements.
        
        AC10 - Response Time:
        - Generate summary results within 5 seconds for standard weekly dataset
        
        Tests key reporting queries to ensure they complete within timeout.
        
        Time Complexity: Query dependent (should all be < 5 seconds)
        Space Complexity: O(n) for result sets
        
        Returns:
            dict: Performance test results
            {
                'all_pass': bool,
                'tests': {
                    'production_line_issues': {time: float, pass: bool},
                    'defect_trends': {time: float, pass: bool},
                    'shipment_status': {time: float, pass: bool}
                },
                'timeout_seconds': float
            }
        """
        import time
        from datetime import date, timedelta
        
        timeout = Config.QUERY_TIMEOUT_SECONDS
        results = {
            'all_pass': True,
            'tests': {},
            'timeout_seconds': timeout
        }
        
        try:
            # Test 1: Production line issues for one week
            start = time.time()
            from reporter import Reporter
            week_start = date.today() - timedelta(days=7)
            Reporter.get_production_line_issues(week_start, date.today())
            elapsed = time.time() - start
            
            results['tests']['production_line_issues'] = {
                'time_seconds': round(elapsed, 2),
                'pass': elapsed < timeout
            }
            if not results['tests']['production_line_issues']['pass']:
                results['all_pass'] = False
            
            # Test 2: Defect trends for past 30 days
            start = time.time()
            Reporter.get_defect_trends(30)
            elapsed = time.time() - start
            
            results['tests']['defect_trends'] = {
                'time_seconds': round(elapsed, 2),
                'pass': elapsed < timeout
            }
            if not results['tests']['defect_trends']['pass']:
                results['all_pass'] = False
            
            # Test 3: Shipment status summary
            start = time.time()
            Reporter.get_shipment_status_summary()
            elapsed = time.time() - start
            
            results['tests']['shipment_status'] = {
                'time_seconds': round(elapsed, 2),
                'pass': elapsed < timeout
            }
            if not results['tests']['shipment_status']['pass']:
                results['all_pass'] = False
            
        except Exception as e:
            logger.error(f"Performance validation error: {e}")
            results['all_pass'] = False
            results['error'] = str(e)
        
        return results
    
    @staticmethod
    def get_discrepancies(limit=100):
        """
        Retrieves recorded data discrepancies for review.
        
        Time Complexity: O(n)
        Space Complexity: O(n)
        
        Args:
            limit (int): Maximum number of discrepancies to return
        
        Returns:
            list: Discrepancy records
        """
        try:
            query = """
            SELECT data_discrepancy_id, lot_id, missing_in_source, description, resolution_status
            FROM data_discrepancies
            WHERE resolution_status = 'Open'
            ORDER BY created_at DESC
            LIMIT %s
            """
            
            results = Database.execute_query(query, (limit,))
            
            return [
                {
                    'discrepancy_id': r[0],
                    'lot_id': r[1],
                    'missing_in_source': r[2],
                    'description': r[3],
                    'resolution_status': r[4]
                }
                for r in results
            ]
            
        except Error as e:
            logger.error(f"Failed to get discrepancies: {e}")
            return []
    
    @staticmethod
    def resolve_discrepancy(discrepancy_id, status='Resolved'):
        """
        Marks a discrepancy as resolved.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Args:
            discrepancy_id (int): Discrepancy ID to resolve
            status (str): Resolution status ('Resolved', 'Reviewed', etc.)
        
        Returns:
            bool: True if successful
        """
        try:
            update_sql = """
            UPDATE data_discrepancies
            SET resolution_status = %s
            WHERE data_discrepancy_id = %s
            """
            
            Database.execute_update(update_sql, (status, discrepancy_id))
            return True
            
        except Error as e:
            logger.error(f"Failed to resolve discrepancy: {e}")
            return False


if __name__ == '__main__':
    print("Data Validator Module - Ensures data consistency and integrity")
