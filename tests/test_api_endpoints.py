"""
Unit tests for FastAPI endpoints.

Tests merge operations, undo functionality, and API responses.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.main import app


class TestMergeEndpoints:
    """Test suite for merge-related API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.test_org_id = "test_org_12345"
        self.test_credentials = {
            "base_url": "https://test.atlassian.net",
            "username": "test@example.com",
            "api_token": "test_token"
        }
    
    @patch('services.main.MergeOperationsStorage')
    def test_get_merge_history_success(self, mock_storage_class):
        """Test successful merge history retrieval."""
        # Mock storage instance
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        
        # Mock return data
        mock_history = [
            {
                'id': 'merge_001',
                'organization_id': self.test_org_id,
                'page_id': 'page_123',
                'duplicate_page_id': 'page_456',
                'timestamp': '2024-01-01T10:00:00Z',
                'status': 'completed'
            }
        ]
        mock_storage.get_merge_history.return_value = mock_history
        
        # Make request
        response = self.client.get(f"/merge/history?organization_id={self.test_org_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['id'] == 'merge_001'
        
        # Verify storage was called correctly
        mock_storage.get_merge_history.assert_called_once_with(self.test_org_id)
    
    def test_get_merge_history_missing_org_id(self):
        """Test merge history request without organization_id."""
        response = self.client.get("/merge/history")
        assert response.status_code == 400
        assert "organization_id is required" in response.json()["detail"]
    
    @patch('services.main.MergeOperationsStorage')
    @patch('services.main.apply_merge_to_confluence')
    def test_undo_merge_success(self, mock_apply_merge, mock_storage_class):
        """Test successful merge undo operation."""
        # Mock storage
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        
        # Mock validation success
        mock_storage.validate_undo_sequence.return_value = {
            'can_undo': True,
            'requires_sequential_undo': False,
            'reason': 'Valid for undo'
        }
        
        # Mock merge operation
        mock_merge_operation = {
            'id': 'merge_001',
            'page_id': 'page_123',
            'duplicate_page_id': 'page_456',
            'pre_merge_version': 5
        }
        mock_storage.get_merge_operation.return_value = mock_merge_operation
        
        # Mock Confluence undo success
        mock_apply_merge.return_value = True
        
        # Prepare request data
        request_data = {
            "merge_id": "merge_001",
            "organization_id": self.test_org_id,
            "credentials": self.test_credentials
        }
        
        # Make request
        response = self.client.post("/merge/undo", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "successfully undone" in data["message"]
        
        # Verify storage methods were called
        mock_storage.validate_undo_sequence.assert_called_once_with("merge_001", self.test_org_id)
        mock_storage.mark_operation_undone.assert_called_once_with("merge_001", self.test_org_id)
    
    @patch('services.main.MergeOperationsStorage')
    def test_undo_merge_sequential_validation_failure(self, mock_storage_class):
        """Test undo operation that fails sequential validation."""
        # Mock storage
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        
        # Mock validation failure
        mock_storage.validate_undo_sequence.return_value = {
            'can_undo': False,
            'requires_sequential_undo': True,
            'reason': 'Must undo more recent operations first',
            'next_required_undo': {
                'id': 'merge_002',
                'timestamp': '2024-01-01T11:00:00Z'
            },
            'blocking_operations': [
                {'id': 'merge_002', 'timestamp': '2024-01-01T11:00:00Z'}
            ]
        }
        
        # Prepare request data
        request_data = {
            "merge_id": "merge_001",
            "organization_id": self.test_org_id,
            "credentials": self.test_credentials
        }
        
        # Make request
        response = self.client.post("/merge/undo", json=request_data)
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["requires_sequential_undo"] is True
        assert data["next_required_undo"]["id"] == "merge_002"
    
    def test_undo_merge_missing_fields(self):
        """Test undo request with missing required fields."""
        # Missing merge_id
        response = self.client.post("/merge/undo", json={
            "organization_id": self.test_org_id,
            "credentials": self.test_credentials
        })
        assert response.status_code == 422  # Validation error
        
        # Missing organization_id
        response = self.client.post("/merge/undo", json={
            "merge_id": "merge_001",
            "credentials": self.test_credentials
        })
        assert response.status_code == 422
        
        # Missing credentials
        response = self.client.post("/merge/undo", json={
            "merge_id": "merge_001",
            "organization_id": self.test_org_id
        })
        assert response.status_code == 422


class TestConfluenceIntegration:
    """Test Confluence API integration functions."""
    
    @patch('confluence.api.requests.get')
    def test_get_page_version_success(self, mock_get):
        """Test successful page version retrieval."""
        from confluence.api import get_page_version
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'version': {'number': 5}
        }
        mock_get.return_value = mock_response
        
        # Test the function
        credentials = ("test@example.com", "token")
        version = get_page_version("page_123", "https://test.atlassian.net", credentials)
        
        assert version == 5
        mock_get.assert_called_once()
    
    @patch('confluence.api.requests.get')
    def test_get_page_version_failure(self, mock_get):
        """Test page version retrieval failure."""
        from confluence.api import get_page_version
        
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Test the function
        credentials = ("test@example.com", "token")
        version = get_page_version("nonexistent_page", "https://test.atlassian.net", credentials)
        
        assert version is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
