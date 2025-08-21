"""
Merge operations storage service with S3 and local filesystem fallback.
Handles organization-specific merge history with sequential undo validation.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
import uuid

# Make boto3 optional for local development
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None

logger = logging.getLogger(__name__)

class MergeOperationsStorage:
    def __init__(self):
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'concatly-duplicates')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.local_storage_path = Path(os.getenv('LOCAL_STORAGE_PATH', './local_storage'))
        
        # Try to initialize S3, fall back to local if it fails
        self.use_s3 = self._init_s3()
        
        if not self.use_s3:
            logger.info(f"📁 Using local storage for merge operations at: {self.local_storage_path}")
            self.local_storage_path.mkdir(exist_ok=True)
        else:
            logger.info(f"☁️ Using S3 bucket for merge operations: {self.bucket_name}")
    
    def _init_s3(self) -> bool:
        """Initialize S3 client and test connection."""
        try:
            # Check if boto3 is available
            if not HAS_BOTO3:
                logger.info("📦 boto3 not installed, using local storage for merge operations")
                return False
            
            # Check for AWS credentials
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if not aws_access_key or not aws_secret_key:
                logger.info("🔑 AWS credentials not found, using local storage for merge operations")
                return False
            
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=self.aws_region
            )
            
            # Test connection
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info("✅ S3 connection successful for merge operations")
                return True
            except Exception as e:
                logger.warning(f"❌ S3 bucket access failed: {e}")
                return False
                
        except Exception as e:
            logger.warning(f"❌ S3 initialization failed: {e}")
            return False
    
    def _get_org_merge_operations_path(self, organization_id: str) -> str:
        """Get the file path for organization's merge operations."""
        return f"{organization_id}/merge_operations.json"
    
    def _get_local_merge_operations_file(self, organization_id: str) -> Path:
        """Get local file path for organization's merge operations."""
        org_dir = self.local_storage_path / organization_id
        org_dir.mkdir(exist_ok=True)
        return org_dir / "merge_operations.json"
    
    def get_merge_operations(self, organization_id: str) -> Dict[str, Any]:
        """
        Get all merge operations for an organization.
        
        Args:
            organization_id: The organization ID
            
        Returns:
            Dict containing merge operations data
        """
        if self.use_s3:
            return self._get_merge_operations_s3(organization_id)
        else:
            return self._get_merge_operations_local(organization_id)
    
    def _get_merge_operations_s3(self, organization_id: str) -> Dict[str, Any]:
        """Get merge operations from S3."""
        try:
            key = self._get_org_merge_operations_path(organization_id)
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except self.s3_client.exceptions.NoSuchKey:
            logger.info(f"📝 No merge operations found for org {organization_id}, creating new file")
            return {"operations": [], "organization_id": organization_id, "created_at": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"❌ Failed to get merge operations from S3: {e}")
            # Fallback to local
            return self._get_merge_operations_local(organization_id)
    
    def _get_merge_operations_local(self, organization_id: str) -> Dict[str, Any]:
        """Get merge operations from local storage."""
        try:
            file_path = self._get_local_merge_operations_file(organization_id)
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                logger.info(f"📝 No local merge operations found for org {organization_id}, creating new file")
                return {"operations": [], "organization_id": organization_id, "created_at": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"❌ Failed to read local merge operations: {e}")
            return {"operations": [], "organization_id": organization_id, "created_at": datetime.now().isoformat()}
    
    def save_merge_operations(self, organization_id: str, merge_data: Dict[str, Any]) -> bool:
        """
        Save merge operations for an organization.
        
        Args:
            organization_id: The organization ID
            merge_data: The complete merge operations data
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Ensure organization_id is set
        merge_data["organization_id"] = organization_id
        merge_data["updated_at"] = datetime.now().isoformat()
        
        if self.use_s3:
            success = self._save_merge_operations_s3(organization_id, merge_data)
            if not success:
                # Fallback to local
                return self._save_merge_operations_local(organization_id, merge_data)
            return success
        else:
            return self._save_merge_operations_local(organization_id, merge_data)
    
    def _save_merge_operations_s3(self, organization_id: str, merge_data: Dict[str, Any]) -> bool:
        """Save merge operations to S3."""
        try:
            key = self._get_org_merge_operations_path(organization_id)
            content = json.dumps(merge_data, indent=2)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType='application/json'
            )
            
            logger.info(f"💾 Saved merge operations to S3 for org {organization_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save merge operations to S3: {e}")
            return False
    
    def _save_merge_operations_local(self, organization_id: str, merge_data: Dict[str, Any]) -> bool:
        """Save merge operations to local storage."""
        try:
            file_path = self._get_local_merge_operations_file(organization_id)
            with open(file_path, 'w') as f:
                json.dump(merge_data, f, indent=2)
            
            logger.info(f"💾 Saved merge operations locally for org {organization_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save merge operations locally: {e}")
            return False
    
    def add_merge_operation(self, organization_id: str, operation_data: Dict[str, Any]) -> str:
        """
        Add a new merge operation.
        
        Args:
            organization_id: The organization ID
            operation_data: The merge operation data
            
        Returns:
            str: The operation ID
        """
        # Generate operation ID if not provided
        if 'id' not in operation_data:
            operation_data['id'] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if 'timestamp' not in operation_data:
            operation_data['timestamp'] = datetime.now().isoformat()
        
        # Get current operations
        merge_data = self.get_merge_operations(organization_id)
        
        # Add the new operation
        merge_data['operations'].append(operation_data)
        
        # Save updated data
        self.save_merge_operations(organization_id, merge_data)
        
        return operation_data['id']
    
    def update_merge_operation(self, organization_id: str, operation_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing merge operation.
        
        Args:
            organization_id: The organization ID
            operation_id: The operation ID to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful, False if operation not found
        """
        merge_data = self.get_merge_operations(organization_id)
        
        # Find and update the operation
        for operation in merge_data['operations']:
            if operation.get('id') == operation_id:
                operation.update(updates)
                operation['updated_at'] = datetime.now().isoformat()
                
                # Save updated data
                self.save_merge_operations(organization_id, merge_data)
                return True
        
        logger.warning(f"❌ Merge operation {operation_id} not found for org {organization_id}")
        return False
    
    def get_merge_operation(self, organization_id: str, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific merge operation.
        
        Args:
            organization_id: The organization ID
            operation_id: The operation ID
            
        Returns:
            Dict or None: The operation data if found
        """
        merge_data = self.get_merge_operations(organization_id)
        
        for operation in merge_data['operations']:
            if operation.get('id') == operation_id:
                return operation
        
        return None
    
    def get_page_merge_chain(self, organization_id: str, page_id: str) -> List[Dict[str, Any]]:
        """
        Get all merge operations involving a specific page, ordered chronologically.
        This helps determine merge dependencies for sequential undo validation.
        
        Args:
            organization_id: The organization ID
            page_id: The Confluence page ID
            
        Returns:
            List of merge operations involving this page, ordered by timestamp
        """
        merge_data = self.get_merge_operations(organization_id)
        
        # Find operations where this page was involved
        page_operations = []
        for operation in merge_data['operations']:
            if (operation.get('kept_page_id') == page_id or 
                operation.get('deleted_page_id') == page_id or
                operation.get('target_page_id') == page_id or
                operation.get('page_id') == page_id):  # Also check for page_id
                page_operations.append(operation)
        
        # Sort by timestamp
        page_operations.sort(key=lambda x: x.get('timestamp', ''))
        
        return page_operations
    
    def validate_undo_sequence(self, organization_id: str, operation_id: str) -> Dict[str, Any]:
        """
        Validate if an operation can be undone without breaking the merge chain.
        
        Args:
            organization_id: The organization ID
            operation_id: The operation ID to undo
            
        Returns:
            Dict with validation result and required actions
        """
        operation = self.get_merge_operation(organization_id, operation_id)
        if not operation:
            return {
                "can_undo": False,
                "reason": "Operation not found",
                "required_undos": [],
                "requires_sequential_undo": False
            }
        
        if operation.get('status') != 'completed':
            return {
                "can_undo": False,
                "reason": f"Operation status is '{operation.get('status')}', can only undo completed operations",
                "required_undos": [],
                "requires_sequential_undo": False
            }
        
        # Get the page ID that was kept/modified
        target_page_id = (operation.get('kept_page_id') or 
                         operation.get('target_page_id') or 
                         operation.get('page_id'))  # Also check for page_id
        if not target_page_id:
            return {
                "can_undo": False,
                "reason": "Cannot determine target page for operation",
                "required_undos": [],
                "requires_sequential_undo": False
            }
        
        # Get all operations involving this page
        page_operations = self.get_page_merge_chain(organization_id, target_page_id)
        
        # Find operations that came after this one and are still completed
        operation_timestamp = operation.get('timestamp', '')
        blocking_operations = []
        
        for later_op in page_operations:
            later_timestamp = later_op.get('timestamp', '')
            if (later_timestamp > operation_timestamp and 
                later_op.get('status') == 'completed' and
                later_op.get('id') != operation_id):
                blocking_operations.append(later_op)
        
        if blocking_operations:
            return {
                "can_undo": False,
                "reason": "Later merge operations must be undone first to maintain data integrity",
                "required_undos": blocking_operations,
                "requires_sequential_undo": True,
                "next_required_undo": blocking_operations[-1]  # Most recent blocking operation
            }
        
        return {
            "can_undo": True,
            "reason": "Operation can be safely undone",
            "required_undos": [],
            "requires_sequential_undo": False
        }
    
    def get_merge_history(self, organization_id: str) -> List[Dict[str, Any]]:
        """
        Get merge history for an organization (alias for get_merge_operations).
        
        Args:
            organization_id: The organization ID
            
        Returns:
            List of merge operations
        """
        merge_data = self.get_merge_operations(organization_id)
        return merge_data.get('operations', [])
    
    def mark_operation_undone(self, operation_id: str, organization_id: str) -> bool:
        """
        Mark an operation as undone.
        
        Args:
            operation_id: The operation ID to mark as undone
            organization_id: The organization ID
            
        Returns:
            bool: True if successful
        """
        return self.update_merge_operation(organization_id, operation_id, {'status': 'undone'})
    
    def store_merge_operation(self, merge_data: Dict[str, Any]) -> str:
        """
        Compatibility method for tests - stores a merge operation.
        
        Args:
            merge_data: Should contain 'organization_id' and operation data
            
        Returns:
            str: Operation ID
        """
        org_id = merge_data.get('organization_id')
        if not org_id:
            raise ValueError("organization_id is required in merge_data")
        
        # Remove organization_id from the data before storing
        operation_data = {k: v for k, v in merge_data.items() if k != 'organization_id'}
        
        # If the test provides an 'id', we need to store it directly rather than generate one
        if 'id' in operation_data:
            provided_id = operation_data['id']
            # Get existing operations for this org
            merge_ops = self.get_merge_operations(org_id)
            
            # Add this operation to the list
            merge_ops['operations'].append(operation_data)
            merge_ops['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Save back
            self.save_merge_operations(org_id, merge_ops)
            return provided_id
        else:
            # Use the normal add method
            return self.add_merge_operation(org_id, operation_data)

# Global instance
merge_operations_storage = MergeOperationsStorage()
