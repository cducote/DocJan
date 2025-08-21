"""
Simple unit tests for MergeOperationsStorage service.

Tests basic functionality and organization isolation.
"""

import pytest
import tempfile
import shutil
import os
import json
from datetime import datetime, timezone
from unittest.mock import patch

# Add parent directory to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.merge_operations_storage import MergeOperationsStorage


class TestMergeOperationsStorageBasic:
    """Basic test suite for MergeOperationsStorage service."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_org_id = "test_org_12345"
        self.test_org_id_2 = "test_org_67890"
        
        # Initialize storage with temp directory
        with patch.dict(os.environ, {'LOCAL_STORAGE_PATH': self.temp_dir}):
            self.storage = MergeOperationsStorage()
    
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_and_get_merge_operation(self):
        """Test basic add and retrieve functionality."""
        # Create a merge operation
        merge_data = {
            'page_id': 'page_123',
            'duplicate_page_id': 'page_456',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'completed'
        }
        
        # Add the operation
        operation_id = self.storage.add_merge_operation(self.test_org_id, merge_data)
        
        # Verify it was added
        assert operation_id is not None
        assert isinstance(operation_id, str)
        
        # Retrieve the operation
        retrieved_operation = self.storage.get_merge_operation(self.test_org_id, operation_id)
        
        # Verify the data
        assert retrieved_operation is not None
        assert retrieved_operation['page_id'] == 'page_123'
        assert retrieved_operation['duplicate_page_id'] == 'page_456'
        assert retrieved_operation['status'] == 'completed'
    
    def test_organization_isolation(self):
        """Test that different organizations have isolated storage."""
        # Create operations for two different organizations
        merge_data_1 = {
            'page_id': 'page_123',
            'duplicate_page_id': 'page_456'
        }
        
        merge_data_2 = {
            'page_id': 'page_789',
            'duplicate_page_id': 'page_101'
        }
        
        # Add operations for both organizations
        op_id_1 = self.storage.add_merge_operation(self.test_org_id, merge_data_1)
        op_id_2 = self.storage.add_merge_operation(self.test_org_id_2, merge_data_2)
        
        # Verify each organization only sees their own operations
        operations_1 = self.storage.get_merge_operations(self.test_org_id)
        operations_2 = self.storage.get_merge_operations(self.test_org_id_2)
        
        # Check that each org has exactly one operation
        assert len(operations_1.get('operations', [])) == 1
        assert len(operations_2.get('operations', [])) == 1
        
        # Check that they can't see each other's operations
        # operations are stored as a list, not a dict
        ops_1_ids = [op['id'] for op in operations_1.get('operations', [])]
        ops_2_ids = [op['id'] for op in operations_2.get('operations', [])]
        
        assert op_id_1 in ops_1_ids
        assert op_id_2 not in ops_1_ids
        
        assert op_id_2 in ops_2_ids
        assert op_id_1 not in ops_2_ids
    
    def test_update_merge_operation(self):
        """Test updating an existing merge operation."""
        # Create a merge operation
        merge_data = {
            'page_id': 'page_123',
            'duplicate_page_id': 'page_456',
            'status': 'pending'
        }
        
        # Add the operation
        operation_id = self.storage.add_merge_operation(self.test_org_id, merge_data)
        
        # Update the operation
        updates = {'status': 'completed', 'result': 'success'}
        result = self.storage.update_merge_operation(self.test_org_id, operation_id, updates)
        
        assert result is True
        
        # Verify the update
        updated_operation = self.storage.get_merge_operation(self.test_org_id, operation_id)
        assert updated_operation['status'] == 'completed'
        assert updated_operation['result'] == 'success'
        assert updated_operation['page_id'] == 'page_123'  # Original data preserved
    
    def test_get_page_merge_chain(self):
        """Test getting merge chain for a specific page."""
        # Create multiple merges for the same page
        page_id = 'page_123'
        
        merge_data_1 = {
            'page_id': page_id,
            'duplicate_page_id': 'page_456',
            'timestamp': '2024-01-01T10:00:00Z'
        }
        
        merge_data_2 = {
            'page_id': page_id,
            'duplicate_page_id': 'page_789',
            'timestamp': '2024-01-01T11:00:00Z'
        }
        
        # Add a merge for a different page (should not appear in chain)
        merge_data_3 = {
            'page_id': 'page_999',
            'duplicate_page_id': 'page_888',
            'timestamp': '2024-01-01T12:00:00Z'
        }
        
        # Add all operations
        op_id_1 = self.storage.add_merge_operation(self.test_org_id, merge_data_1)
        op_id_2 = self.storage.add_merge_operation(self.test_org_id, merge_data_2)
        op_id_3 = self.storage.add_merge_operation(self.test_org_id, merge_data_3)
        
        # Get merge chain for page_123
        chain = self.storage.get_page_merge_chain(self.test_org_id, page_id)
        
        # Should only include the two operations for page_123
        assert len(chain) == 2
        
        # Verify the operations in the chain
        chain_ids = {op['id'] for op in chain}
        assert op_id_1 in chain_ids
        assert op_id_2 in chain_ids
        assert op_id_3 not in chain_ids
    
    def test_validate_undo_sequence_basic(self):
        """Test basic undo sequence validation."""
        # Create a merge operation
        merge_data = {
            'page_id': 'page_123',
            'duplicate_page_id': 'page_456',
            'status': 'completed'
        }
        
        # Add the operation
        operation_id = self.storage.add_merge_operation(self.test_org_id, merge_data)
        
        # Test validation
        validation_result = self.storage.validate_undo_sequence(self.test_org_id, operation_id)
        
        # Should be able to undo a single operation
        assert validation_result['can_undo'] is True
        assert validation_result['requires_sequential_undo'] is False
    
    def test_nonexistent_operation(self):
        """Test handling of non-existent operations."""
        # Try to get a non-existent operation
        result = self.storage.get_merge_operation(self.test_org_id, "nonexistent_id")
        assert result is None
        
        # Try to update a non-existent operation
        update_result = self.storage.update_merge_operation(self.test_org_id, "nonexistent_id", {'status': 'test'})
        assert update_result is False
    
    def test_empty_organization(self):
        """Test handling of empty organization data."""
        # Get operations for organization with no data
        operations = self.storage.get_merge_operations("empty_org")
        
        # Should return structure with empty operations list
        assert 'operations' in operations
        assert operations['operations'] == []
        assert operations['organization_id'] == "empty_org"
        
        # Get page merge chain for empty organization
        chain = self.storage.get_page_merge_chain("empty_org", "page_123")
        assert chain == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
