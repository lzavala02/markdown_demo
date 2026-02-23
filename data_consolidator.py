"""
Data Consolidator Module
========================
Consolidates production, quality, and shipping data (AC2).

Implements:
- Unified data view combining all three sources
- Record matching via normalized Lot IDs
- Secondary matching via production date
- Data consistency checking

AC2 - Unified Data View:
- Combine production, quality, and shipping data
- Match records using Lot ID and/or production date
- Create consolidated view for reporting

Time Complexity: O(n log n) for join operations where n = number of records
Space Complexity: O(n) for consolidated dataset
"""

import logging
from database import Database
from data_normalizer import LotIDNormalizer, LotIDMatcher
from psycopg2 import Error

logger = logging.getLogger(__name__)


class ConsolidatedView:
    """
    Provides consolidated view of production, quality, and shipping data.
    
    This class implements AC2 by joining data from three sources using:
    - Primary key: Normalized Lot ID
    - Secondary key: Production date
    
    Structure:
    {
        'lot_id': database lot_id,
        'lot_number': normalized business lot number,
        'production_date': date,
        'production_line': line name,
        'production_records': [list of production records],
        'quality_records': [list of quality inspection records],
        'shipping_record': shipping status record
    }
    """
    
    @staticmethod
    def get_consolidated_lot(lot_id_or_number):
        """
        Retrieves consolidated data for a single lot.
        
        Fetches data from all three sources and combines them into
        a single unified view.
        
        Time Complexity: O(n) where n = total records for this lot
        Space Complexity: O(n) for result structure
        
        Args:
            lot_id_or_number (str or int): Lot ID (number) or normalized lot number
        
        Returns:
            dict: Consolidated lot data or None if not found
        """
        try:
            # Get lot details
            if isinstance(lot_id_or_number, int):
                lot_query = "SELECT lot_id, business_lot_number, production_date, production_line_id FROM lots WHERE lot_id = %s"
                lot_params = (lot_id_or_number,)
            else:
                normalized = LotIDNormalizer.normalize(lot_id_or_number)
                lot_query = "SELECT lot_id, business_lot_number, production_date, production_line_id FROM lots WHERE business_lot_number = %s"
                lot_params = (normalized,)
            
            lot_results = Database.execute_query(lot_query, lot_params)
            if not lot_results:
                return None
            
            lot_id, lot_number, prod_date, line_id = lot_results[0]
            
            # Get production line name
            line_query = "SELECT line_name FROM production_lines WHERE production_line_id = %s"
            line_results = Database.execute_query(line_query, (line_id,))
            production_line = line_results[0][0] if line_results else "Unknown"
            
            # Build consolidated view
            consolidated = {
                'lot_id': lot_id,
                'lot_number': lot_number,
                'production_date': prod_date,
                'production_line': production_line,
                'production_records': ConsolidatedView._get_production_records(lot_id),
                'quality_records': ConsolidatedView._get_quality_records(lot_id),
                'shipping_record': ConsolidatedView._get_shipping_record(lot_id),
                'summary': {}
            }
            
            # Add summary statistics
            consolidated['summary'] = ConsolidatedView._calculate_summary(consolidated)
            
            return consolidated
            
        except Error as e:
            logger.error(f"Failed to get consolidated lot: {e}")
            return None
    
    @staticmethod
    def _get_production_records(lot_id):
        """
        Gets all production records for a lot.
        
        Time Complexity: O(p) where p = production record count
        Space Complexity: O(p)
        
        Args:
            lot_id (int): Lot ID
        
        Returns:
            list: Production records
        """
        query = """
        SELECT production_record_id, lot_id, production_line_id, production_date,
               record_timestamp, quantity_produced, status, issue_description
        FROM production_records
        WHERE lot_id = %s
        ORDER BY record_timestamp DESC
        """
        
        results = Database.execute_query(query, (lot_id,))
        return [
            {
                'record_id': r[0],
                'lot_id': r[1],
                'production_line_id': r[2],
                'production_date': r[3],
                'timestamp': r[4],
                'quantity_produced': r[5],
                'status': r[6],
                'issue_description': r[7]
            }
            for r in results
        ]
    
    @staticmethod
    def _get_quality_records(lot_id):
        """
        Gets all quality inspection records for a lot.
        
        Time Complexity: O(q) where q = quality record count
        Space Complexity: O(q)
        
        Args:
            lot_id (int): Lot ID
        
        Returns:
            list: Quality records with defect type names
        """
        query = """
        SELECT qr.quality_record_id, qr.lot_id, qr.inspection_date,
               dt.defect_name, qr.defect_count, qr.inspection_status, 
               qr.inspector, qr.notes
        FROM quality_records qr
        JOIN defect_types dt ON qr.defect_type_id = dt.defect_type_id
        WHERE qr.lot_id = %s
        ORDER BY qr.inspection_date DESC
        """
        
        results = Database.execute_query(query, (lot_id,))
        return [
            {
                'record_id': r[0],
                'lot_id': r[1],
                'inspection_date': r[2],
                'defect_type': r[3],
                'defect_count': r[4],
                'inspection_status': r[5],
                'inspector': r[6],
                'notes': r[7]
            }
            for r in results
        ]
    
    @staticmethod
    def _get_shipping_record(lot_id):
        """
        Gets shipping record for a lot (typically 0-1 records).
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        
        Args:
            lot_id (int): Lot ID
        
        Returns:
            dict: Shipping record or None
        """
        query = """
        SELECT shipping_record_id, lot_id, shipment_date, shipment_status,
               carrier_info, destination
        FROM shipping_records
        WHERE lot_id = %s
        LIMIT 1
        """
        
        results = Database.execute_query(query, (lot_id,))
        if not results:
            return None
        
        r = results[0]
        return {
            'record_id': r[0],
            'lot_id': r[1],
            'shipment_date': r[2],
            'shipment_status': r[3],
            'carrier_info': r[4],
            'destination': r[5]
        }
    
    @staticmethod
    def _calculate_summary(consolidated):
        """
        Calculates summary statistics for consolidated lot.
        
        Time Complexity: O(n) where n = total records
        Space Complexity: O(1)
        
        Args:
            consolidated (dict): Consolidated lot data
        
        Returns:
            dict: Summary with totals and statuses
        """
        summary = {
            'total_production_records': len(consolidated['production_records']),
            'total_quality_records': len(consolidated['quality_records']),
            'total_defects': sum(r['defect_count'] for r in consolidated['quality_records']),
            'total_quantity_produced': sum(r['quantity_produced'] for r in consolidated['production_records']),
            'has_shipping_record': consolidated['shipping_record'] is not None,
            'shipment_status': consolidated['shipping_record']['shipment_status'] if consolidated['shipping_record'] else 'No Record',
            'pass_count': sum(1 for r in consolidated['quality_records'] if r['inspection_status'] == 'Pass'),
            'fail_count': sum(1 for r in consolidated['quality_records'] if r['inspection_status'] == 'Fail'),
        }
        
        return summary
    
    @staticmethod
    def get_all_consolidated_lots(filters=None):
        """
        Gets consolidated view for all lots (paginated for performance).
        
        Supports filtering by:
        - production_line
        - production_date (exact or range)
        - shipment_status
        
        Time Complexity: O(n log n) where n = lot count
        Space Complexity: O(n)
        
        Args:
            filters (dict): Optional filter criteria
                {
                    'production_line': str,
                    'production_date_from': date,
                    'production_date_to': date,
                    'shipment_status': str,
                    'limit': int (default 1000),
                    'offset': int (default 0)
                }
        
        Returns:
            list: List of consolidated lots meeting criteria
        """
        filters = filters or {}
        limit = filters.get('limit', 1000)
        offset = filters.get('offset', 0)
        
        # Build base query
        query = """
        SELECT DISTINCT l.lot_id, l.business_lot_number, l.production_date, pl.line_name
        FROM lots l
        LEFT JOIN production_lines pl ON l.production_line_id = pl.production_line_id
        WHERE 1=1
        """
        
        params = []
        
        # Add filters
        if filters.get('production_line'):
            query += " AND LOWER(pl.line_name) = LOWER(%s)"
            params.append(filters['production_line'])
        
        if filters.get('production_date_from'):
            query += " AND l.production_date >= %s"
            params.append(filters['production_date_from'])
        
        if filters.get('production_date_to'):
            query += " AND l.production_date <= %s"
            params.append(filters['production_date_to'])
        
        if filters.get('shipment_status'):
            query += """ AND EXISTS (
                SELECT 1 FROM shipping_records sr 
                WHERE sr.lot_id = l.lot_id AND sr.shipment_status = %s
            )"""
            params.append(filters['shipment_status'])
        
        query += f" ORDER BY l.production_date DESC LIMIT {limit} OFFSET {offset}"
        
        results = Database.execute_query(query, params)
        
        # Convert to consolidated format
        consolidated_lots = []
        for lot_id, lot_number, prod_date, line_name in results:
            consolidated = ConsolidatedView.get_consolidated_lot(lot_id)
            if consolidated:
                consolidated_lots.append(consolidated)
        
        return consolidated_lots


if __name__ == '__main__':
    print("Data Consolidator Module - Creates unified views of production, quality, and shipping data")
