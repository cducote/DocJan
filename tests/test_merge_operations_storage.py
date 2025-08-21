"""
Unit tests for MergeOperationsStorage service.

Tests organization isolation, sequential undo validation, and storage operations.
"""

import pytest
import tempfile
import shutil
import os
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.merge_operations_storage import MergeOperationsStorage


class TestMergeOperationsStorage:
    """Test suite for MergeOperationsStorage service."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_org_id = "test_org_12345"
        self.test_org_id_2 = "test_org_67890"
        
        # Initialize storage with temp directory
        with patch.dict(os.environ, {'LOCAL_STORAGE_BASE': self.temp_dir}):
            self.storage = MergeOperationsStorage()
            
        # Clear any existing data for our test organizations (in case of test isolation failures)
        self.storage.get_merge_operations(self.test_org_id)  # Initialize if needed
        self.storage.save_merge_operations(self.test_org_id, {'operations': [], 'organization_id': self.test_org_id, 'created_at': datetime.now(timezone.utc).isoformat(), 'updated_at': datetime.now(timezone.utc).isoformat()})
        self.storage.get_merge_operations(self.test_org_id_2)  # Initialize if needed  
        self.storage.save_merge_operations(self.test_org_id_2, {'operations': [], 'organization_id': self.test_org_id_2, 'created_at': datetime.now(timezone.utc).isoformat(), 'updated_at': datetime.now(timezone.utc).isoformat()})
    
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_organization_isolation(self):
        """Test that different organizations have isolated storage."""
        # Create merge operations for two different organizations
        merge_data_1 = {
            'page_id': 'page_123',
            'duplicate_page_id': 'page_456',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        merge_data_2 = {
            'page_id': 'page_789',
            'duplicate_page_id': 'page_101', 
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Store operations for both organizations
        merge_id_1 = self.storage.add_merge_operation(self.test_org_id, merge_data_1)
        merge_id_2 = self.storage.add_merge_operation(self.test_org_id_2, merge_data_2)
        
        # Verify each organization only sees their own operations
        operations_1 = self.storage.get_merge_operations(self.test_org_id)
        operations_2 = self.storage.get_merge_operations(self.test_org_id_2)
        
        assert len(operations_1.get('operations', [])) == 1
        assert len(operations_2.get('operations', [])) == 1
        
        # Check that the operation IDs are in the operations (correct data structure)
        op1_ids = [op['id'] for op in operations_1.get('operations', [])]
        op2_ids = [op['id'] for op in operations_2.get('operations', [])]
        
        assert merge_id_1 in op1_ids
        assert merge_id_2 in op2_ids
        assert merge_id_1 not in op2_ids
        assert merge_id_2 not in op1_ids
    
    def test_sequential_undo_validation(self):
        """Test that sequential undo validation works correctly."""
        # Create a chain of merge operations for the same page
        base_time = datetime.now(timezone.utc)
        
        merges = [
            {
                'page_id': 'page_123',
                'duplicate_page_id': 'page_456',
                'timestamp': base_time.isoformat(),
                'status': 'completed'
            },
            {
                'page_id': 'page_123',  # Same page as merge_001
                'duplicate_page_id': 'page_789',
                'timestamp': (base_time.replace(minute=base_time.minute + 1)).isoformat(),
                'status': 'completed'
            },
            {
                'page_id': 'page_123',  # Same page again
                'duplicate_page_id': 'page_101',
                'timestamp': (base_time.replace(minute=base_time.minute + 2)).isoformat(),
                'status': 'completed'
            }
        ]
        
        # Store all merges and collect their IDs
        merge_ids = []
        for merge in merges:
            merge_id = self.storage.add_merge_operation(self.test_org_id, merge)
            merge_ids.append(merge_id)
        
        # Try to undo the first merge (should fail - not the most recent)
        validation_result = self.storage.validate_undo_sequence(self.test_org_id, merge_ids[0])
        
        assert not validation_result['can_undo']
        assert validation_result['requires_sequential_undo']
        # The most recent operation should be the one that needs to be undone first
        assert validation_result['next_required_undo']['id'] == merge_ids[2]
    
    def test_successful_sequential_undo(self):
        """Test successful undo when operations are undone in correct order."""
        # Create merge chain
        base_time = datetime.now(timezone.utc)
        
        merges = [
            {
                'id': 'merge_001',
                'organization_id': self.test_org_id,
                'page_id': 'page_123',
                'duplicate_page_id': 'page_456',
                'timestamp': base_time.isoformat(),
                'status': 'completed'
            },
            {
                'id': 'merge_002',
                'organization_id': self.test_org_id,
                'page_id': 'page_123',
                'duplicate_page_id': 'page_789',
                'timestamp': (base_time.replace(minute=base_time.minute + 1)).isoformat(),
                'status': 'completed'
            }
        ]
        
        for merge in merges:
            self.storage.store_merge_operation(merge)
        
        # Undo most recent first (should succeed)
        validation_result = self.storage.validate_undo_sequence(self.test_org_id, 'merge_002')
        assert validation_result['can_undo']
        
        # Mark as undone
        self.storage.mark_operation_undone('merge_002', self.test_org_id)
        
        # Now undo the first merge (should succeed)
        validation_result = self.storage.validate_undo_sequence(self.test_org_id, 'merge_001')
        assert validation_result['can_undo']
    
    def test_page_merge_chain(self):
        """Test getting merge chain for a specific page."""
        # Create merges for different pages
        merges = [
            {
                'id': 'merge_001',
                'organization_id': self.test_org_id,
                'page_id': 'page_123',
                'duplicate_page_id': 'page_456',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'completed'
            },
            {
                'id': 'merge_002',
                'organization_id': self.test_org_id,
                'page_id': 'page_999',  # Different page
                'duplicate_page_id': 'page_888',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'completed'
            },
            {
                'id': 'merge_003',
                'organization_id': self.test_org_id,
                'page_id': 'page_123',  # Same as merge_001
                'duplicate_page_id': 'page_777',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'completed'
            }
        ]
        
        for merge in merges:
            self.storage.store_merge_operation(merge)
        
        # Get merge chain for page_123 (correct parameter order)
        chain = self.storage.get_page_merge_chain(self.test_org_id, 'page_123')
        
        assert len(chain) == 2  # merge_001 and merge_003
        assert {m['id'] for m in chain} == {'merge_001', 'merge_003'}
    
    @patch('boto3.client')
    def test_s3_fallback(self, mock_boto3):
        """Test S3 storage fallback when configured."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        
        # Configure S3 environment
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret',
            'S3_BUCKET_NAME': 'test-bucket'
        }):
            storage = MergeOperationsStorage()
            
            merge_data = {
                'id': 'merge_001',
                'organization_id': self.test_org_id,
                'page_id': 'page_123',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # This should attempt S3 storage
            storage.store_merge_operation(merge_data)
            
            # Verify S3 put_object was called
            mock_s3.put_object.assert_called_once()
    
    def test_invalid_organization_id(self):
        """Test handling of invalid organization IDs."""
        # Try to get history for non-existent organization
        history = self.storage.get_merge_history("nonexistent_org")
        assert history == []
        
        # Try to validate undo for non-existent organization
        validation = self.storage.validate_undo_sequence("merge_001", "nonexistent_org")
        assert not validation['can_undo']
        assert "not found" in validation['reason'].lower()
    
    def test_concurrent_operations(self):
        """Test handling of concurrent operations on same page."""
        import threading
        import time
        
        def create_merge(merge_id, delay=0):
            if delay:
                time.sleep(delay)
            merge_data = {
                'id': merge_id,
                'organization_id': self.test_org_id,
                'page_id': 'page_123',
                'duplicate_page_id': f'page_{merge_id}',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'completed'
            }
            self.storage.store_merge_operation(merge_data)
        
        # Create concurrent merges
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_merge, args=(f'merge_00{i+1}', i * 0.1))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all operations were stored
        history = self.storage.get_merge_history(self.test_org_id)
        assert len(history) == 3
        assert {h['id'] for h in history} == {'merge_001', 'merge_002', 'merge_003'}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
