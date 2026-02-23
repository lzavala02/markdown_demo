"""
Data Normalizer Module
======================
Handles Lot ID normalization and standardization (AC3).

Implements:
- Lot ID sanitization (trim whitespace, uppercase conversion)
- Ambiguous/unmatched Lot ID detection and flagging
- Normalization audit trail

AC3 - Lot ID Normalization:
- Detect and standardize inconsistent lot ID formatting
- Flag unmatched or ambiguous lot IDs for review

Time Complexity: O(n) where n = number of lot IDs to normalize
Space Complexity: O(n) for storing normalized mappings
"""

import re
import logging
from database import Database
from psycopg2 import Error

logger = logging.getLogger(__name__)


class LotIDNormalizer:
    """
    Normalizes and standardizes Lot IDs across different data sources.
    
    Lot IDs may have inconsistent formatting (spaces, case differences).
    This class implements AC3 by:
    1. Sanitizing IDs (trim, uppercase)
    2. Detecting and flagging ambiguous IDs
    3. Maintaining audit trail of normalizations
    
    Attributes:
        NORMALIZATION_RULES (dict): Regex patterns for ID validation and cleaning
    """
    
    # Normalization rules for various Lot ID formats
    NORMALIZATION_RULES = {
        'trim_whitespace': lambda x: str(x).strip() if x else '',
        'uppercase': lambda x: x.upper() if x else '',
        'remove_extra_spaces': lambda x: re.sub(r'\s+', '-', x) if x else '',
    }
    
    @staticmethod
    def normalize(original_lot_id):
        """
        Normalizes a Lot ID by applying standardization rules.
        
        Process:
        1. Trim whitespace from both ends
        2. Convert to uppercase
        3. Replace multiple spaces with single dash
        4. Remove any special characters except dashes
        
        Time Complexity: O(m) where m = length of lot_id string
        Space Complexity: O(m) for normalized string
        
        Args:
            original_lot_id (str): Raw Lot ID from source data
        
        Returns:
            str: Normalized Lot ID in standard format
        
        Example:
            normalize("  LOT 20260112 001 ") → "LOT-20260112-001"
        """
        if not original_lot_id:
            return None
        
        # Step 1: Trim whitespace
        normalized = LotIDNormalizer.NORMALIZATION_RULES['trim_whitespace'](original_lot_id)
        
        # Step 2: Convert to uppercase
        normalized = LotIDNormalizer.NORMALIZATION_RULES['uppercase'](normalized)
        
        # Step 3: Replace spaces with dashes
        normalized = LotIDNormalizer.NORMALIZATION_RULES['remove_extra_spaces'](normalized)
        
        # Step 4: Remove special characters (keep only alphanumeric and dashes)
        normalized = re.sub(r'[^A-Z0-9\-]', '', normalized)
        
        return normalized
    
    @staticmethod
    def is_ambiguous(lot_id):
        """
        Checks if a Lot ID is ambiguous (too generic or malformed).
        
        Ambiguous IDs:
        - Empty or None
        - Shorter than 5 characters
        - No alphanumeric content
        - All numbers (no context)
        
        Time Complexity: O(m) where m = length of lot_id
        Space Complexity: O(1)
        
        Args:
            lot_id (str): Lot ID to check
        
        Returns:
            tuple: (is_ambiguous, reason) where reason explains why it's ambiguous
        """
        if not lot_id:
            return True, "Empty or None Lot ID"
        
        if len(lot_id) < 5:
            return True, f"Lot ID too short (length: {len(lot_id)}, minimum: 5)"
        
        if not any(c.isalnum() for c in lot_id):
            return True, "No alphanumeric characters found"
        
        # Check if it's purely numeric (needs context like date or line prefix)
        if lot_id.replace('-', '').isdigit() and len(lot_id) < 12:
            return True, "Ambiguous numeric-only ID without date/line context"
        
        return False, ""
    
    @staticmethod
    def record_normalization(original_lot_id, normalized_lot_id, validation_status, flag_reason=None):
        """
        Records the normalization in the audit table (AC3 compliance).
        
        Maintains an audit trail of all Lot ID normalizations for
        traceability and debugging.
        
        Time Complexity: O(1) for database insert
        Space Complexity: O(1)
        
        Args:
            original_lot_id (str): Original Lot ID from source
            normalized_lot_id (str): Normalized Lot ID
            validation_status (str): 'Valid', 'Ambiguous', 'Unmatched'
            flag_reason (str): Optional reason for flagging
        
        Returns:
            bool: True if successfully recorded, False otherwise
        """
        try:
            insert_sql = """
            INSERT INTO lot_id_normalizations 
            (original_lot_number, normalized_lot_number, validation_status, flag_reason)
            VALUES (%s, %s, %s, %s)
            """
            
            Database.execute_update(
                insert_sql,
                (original_lot_id, normalized_lot_id, validation_status, flag_reason)
            )
            logger.info(f"Recorded normalization: {original_lot_id} → {normalized_lot_id}")
            return True
            
        except Error as e:
            logger.error(f"Failed to record normalization: {e}")
            return False
    
    @staticmethod
    def validate_and_flag_lot_ids(lot_ids_list):
        """
        Batch validates a list of Lot IDs and flags problematic ones.
        
        Identifies:
        - Ambiguous Lot IDs (formatting issues)
        - Potentially unmatched Lot IDs (don't exist in master data)
        
        Time Complexity: O(n) where n = number of lot IDs
        Space Complexity: O(n) for results dictionary
        
        Args:
            lot_ids_list (list): List of Lot IDs to validate
        
        Returns:
            dict: {
                'valid': [list of valid lot IDs],
                'ambiguous': [list of ambiguous lot IDs],
                'flags': {lot_id: reason}
            }
        """
        results = {
            'valid': [],
            'ambiguous': [],
            'flags': {}
        }
        
        for lot_id in lot_ids_list:
            normalized = LotIDNormalizer.normalize(lot_id)
            is_ambiguous, reason = LotIDNormalizer.is_ambiguous(normalized)
            
            if is_ambiguous:
                results['ambiguous'].append(normalized)
                results['flags'][normalized] = reason
            else:
                results['valid'].append(normalized)
        
        logger.info(f"Validation complete: {len(results['valid'])} valid, "
                   f"{len(results['ambiguous'])} ambiguous")
        
        return results


class LotIDMatcher:
    """
    Matches Lot IDs across different data sources using normalized identifiers.
    
    Implements AC2 (Unified Data View with record matching):
    - Match records using normalized Lot IDs
    - Secondary matching using production date
    
    Time Complexity: Hash-based matching is O(1) per lookup
    Space Complexity: O(n) for index structure
    """
    
    @staticmethod
    def build_lot_index():
        """
        Builds an in-memory index of all Lots for fast lookups.
        
        Creates a dictionary mapping normalized Lot IDs to their database
        IDs for O(1) lookup performance.
        
        Time Complexity: O(n) where n = number of lots in database
        Space Complexity: O(n) for index dictionary
        
        Returns:
            dict: {normalized_lot_id: lot_record}
        """
        try:
            query = """
            SELECT lot_id, business_lot_number, production_date, production_line_id
            FROM lots
            ORDER BY lot_id
            """
            
            rows = Database.execute_query(query)
            lot_index = {}
            
            for row in rows:
                lot_id, business_number, prod_date, line_id = row
                normalized_id = LotIDNormalizer.normalize(business_number)
                lot_index[normalized_id] = {
                    'lot_id': lot_id,
                    'business_number': business_number,
                    'production_date': prod_date,
                    'production_line_id': line_id
                }
            
            logger.info(f"Built lot index with {len(lot_index)} entries")
            return lot_index
            
        except Error as e:
            logger.error(f"Failed to build lot index: {e}")
            return {}
    
    @staticmethod
    def find_matching_lot(source_lot_id, production_date=None, lot_index=None):
        """
        Finds a matching lot using primary (Lot ID) and secondary (date) criteria.
        
        Matching priority:
        1. Normalized Lot ID exact match
        2. Production date secondary match (if provided)
        3. Return None if no match found
        
        Time Complexity: O(1) for hash lookup
        Space Complexity: O(1)
        
        Args:
            source_lot_id (str): Source Lot ID (may be unnormalized)
            production_date (date): Optional production date for secondary matching
            lot_index (dict): Pre-built lot index (if None, queries database)
        
        Returns:
            dict: Matching lot record or None if not found
        """
        # Build index if not provided
        if lot_index is None:
            lot_index = LotIDMatcher.build_lot_index()
        
        # Normalize the provided Lot ID
        normalized_id = LotIDNormalizer.normalize(source_lot_id)
        
        # Primary match: exact normalized ID
        if normalized_id in lot_index:
            return lot_index[normalized_id]
        
        # Secondary match: if production_date provided, try date-based matching
        if production_date:
            for lot_norm_id, lot_record in lot_index.items():
                if (lot_record['production_date'] == production_date and
                    normalized_id.replace('-', '').replace(str(production_date.year), '', 1) ==
                    lot_norm_id.replace('-', '').replace(str(production_date.year), '', 1)):
                    return lot_record
        
        logger.warning(f"No matching lot found for ID: {source_lot_id}")
        return None


if __name__ == '__main__':
    # Test normalization
    test_ids = [
        "  LOT 20260112 001 ",
        "lot-20260112-002",
        "LOT  20260112  003",
        ""
    ]
    
    print("Testing Lot ID Normalization:")
    for test_id in test_ids:
        normalized = LotIDNormalizer.normalize(test_id)
        is_ambiguous, reason = LotIDNormalizer.is_ambiguous(normalized)
        print(f"  '{test_id}' → '{normalized}' (Ambiguous: {is_ambiguous})")
