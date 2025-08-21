"""
Duplicate pairs storage service with S3 and local filesystem fallback.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Make boto3 optional for local development
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None

logger = logging.getLogger(__name__)

class DuplicateStorageService:
    def __init__(self):
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'concatly-duplicates')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.local_storage_path = Path(os.getenv('LOCAL_STORAGE_PATH', './local_storage'))
        
        # Try to initialize S3, fall back to local if it fails
        self.use_s3 = self._init_s3()
        
        if not self.use_s3:
            logger.info(f"📁 Using local storage at: {self.local_storage_path}")
            self.local_storage_path.mkdir(exist_ok=True)
        else:
            logger.info(f"☁️ Using S3 bucket: {self.bucket_name}")
    
    def _init_s3(self) -> bool:
        """Initialize S3 client and test connection."""
        try:
            # Check if boto3 is available
            if not HAS_BOTO3:
                logger.info("📦 boto3 not installed, using local storage")
                return False
            
            # Check for AWS credentials
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if not aws_access_key or not aws_secret_key:
                logger.info("🔑 AWS credentials not found, using local storage")
                return False
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=self.aws_region
            )
            
            # Test connection by listing buckets
            self.s3_client.list_buckets()
            
            # Check if bucket exists, create if it doesn't
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
            except:
                logger.info(f"🪣 Creating S3 bucket: {self.bucket_name}")
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            
            return True
            
        except Exception as e:
            logger.info(f"⚠️ S3 connection failed ({e}), falling back to local storage")
            return False
    
    def _get_metadata_file_path(self, organization_id: str) -> str:
        """Get the file path/key for organization metadata."""
        return f"metadata/{organization_id}/stats.json"
    
    def _get_local_metadata_file_path(self, organization_id: str) -> Path:
        """Get local filesystem path for organization metadata."""
        org_dir = self.local_storage_path / "metadata" / organization_id
        org_dir.mkdir(parents=True, exist_ok=True)
        return org_dir / "stats.json"
    
    def _get_file_path(self, organization_id: str) -> str:
        """Get the file path/key for duplicate pairs."""
        return f"duplicates/{organization_id}/pairs.json"
    
    def _get_local_file_path(self, organization_id: str) -> Path:
        """Get local filesystem path for duplicate pairs."""
        org_dir = self.local_storage_path / "duplicates" / organization_id
        org_dir.mkdir(parents=True, exist_ok=True)
        return org_dir / "pairs.json"
    
    def store_duplicate_pairs(self, organization_id: str, duplicate_pairs: List[Dict[str, Any]]) -> bool:
        """Store duplicate pairs for an organization."""
        try:
            # Add metadata
            data = {
                "organization_id": organization_id,
                "last_updated": datetime.utcnow().isoformat(),
                "total_pairs": len(duplicate_pairs),
                "duplicate_pairs": duplicate_pairs
            }
            
            json_data = json.dumps(data, indent=2)
            
            if self.use_s3:
                # Store in S3
                key = self._get_file_path(organization_id)
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=json_data,
                    ContentType='application/json'
                )
                logger.info(f"☁️ Stored {len(duplicate_pairs)} duplicate pairs for {organization_id} in S3")
            else:
                # Store locally
                file_path = self._get_local_file_path(organization_id)
                with open(file_path, 'w') as f:
                    f.write(json_data)
                logger.info(f"📁 Stored {len(duplicate_pairs)} duplicate pairs for {organization_id} locally")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store duplicate pairs: {e}")
            return False
    
    def get_duplicate_pairs(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve duplicate pairs for an organization."""
        try:
            if self.use_s3:
                # Get from S3
                key = self._get_file_path(organization_id)
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                json_data = response['Body'].read().decode('utf-8')
                logger.info(f"☁️ Retrieved duplicate pairs for {organization_id} from S3")
            else:
                # Get from local storage
                file_path = self._get_local_file_path(organization_id)
                if not file_path.exists():
                    logger.info(f"📁 No duplicate pairs found for {organization_id}")
                    return None
                
                with open(file_path, 'r') as f:
                    json_data = f.read()
                logger.info(f"📁 Retrieved duplicate pairs for {organization_id} from local storage")
            
            return json.loads(json_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve duplicate pairs: {e}")
            return None
    
    def delete_duplicate_pairs(self, organization_id: str) -> bool:
        """Delete duplicate pairs for an organization."""
        try:
            if self.use_s3:
                # Delete from S3
                key = self._get_file_path(organization_id)
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                logger.info(f"☁️ Deleted duplicate pairs for {organization_id} from S3")
            else:
                # Delete from local storage
                file_path = self._get_local_file_path(organization_id)
                if file_path.exists():
                    file_path.unlink()
                logger.info(f"📁 Deleted duplicate pairs for {organization_id} from local storage")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete duplicate pairs: {e}")
            return False
    
    def mark_pair_resolved(self, organization_id: str, pair_id: str) -> bool:
        """Mark a specific duplicate pair as resolved and update metadata counts."""
        try:
            # Get current data
            data = self.get_duplicate_pairs(organization_id)
            if not data:
                logger.error(f"❌ No duplicate pairs found for {organization_id}")
                return False
            
            # Find and mark the pair as resolved
            pairs = data.get('duplicate_pairs', [])
            updated = False
            
            for pair in pairs:
                if str(pair.get('id')) == str(pair_id):
                    pair['status'] = 'resolved'
                    pair['is_resolved'] = True
                    pair['resolved_at'] = datetime.utcnow().isoformat()
                    updated = True
                    logger.info(f"✅ Marked pair {pair_id} as resolved")
                    break
            
            if not updated:
                logger.error(f"❌ Pair {pair_id} not found for {organization_id}")
                return False
            
            # Store updated pairs data
            data['last_updated'] = datetime.utcnow().isoformat()
            pairs_stored = self.store_duplicate_pairs(organization_id, pairs)
            
            if pairs_stored:
                # Update metadata counts
                try:
                    metadata = self.get_organization_metadata(organization_id)
                    if metadata:
                        # Calculate new counts
                        pending_count = sum(1 for pair in pairs if pair.get('status') == 'pending')
                        resolved_count = sum(1 for pair in pairs if pair.get('status') == 'resolved')
                        
                        # Update metadata
                        metadata['pending_duplicate_pairs'] = pending_count
                        metadata['resolved_duplicate_pairs'] = resolved_count
                        metadata['last_modified'] = datetime.utcnow().isoformat()
                        
                        # Store updated metadata
                        metadata_stored = self.store_organization_metadata(organization_id, metadata)
                        if metadata_stored:
                            logger.info(f"✅ Updated metadata counts - pending: {pending_count}, resolved: {resolved_count}")
                        else:
                            logger.warning(f"⚠️ Failed to update metadata counts")
                            
                except Exception as meta_error:
                    logger.error(f"⚠️ Failed to update metadata after marking pair resolved: {meta_error}")
                    # Don't fail the entire operation since the pair was marked as resolved
            
            return pairs_stored
            
        except Exception as e:
            logger.error(f"❌ Failed to mark pair as resolved: {e}")
            return False
    
    def get_unresolved_pairs(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get only unresolved duplicate pairs."""
        data = self.get_duplicate_pairs(organization_id)
        if not data:
            return []
        
        pairs = data.get('duplicate_pairs', [])
        # Check both 'status' field and 'is_resolved' for compatibility
        unresolved = [
            pair for pair in pairs 
            if pair.get('status') == 'pending' or (not pair.get('is_resolved', False) and pair.get('status') != 'resolved')
        ]
        
        logger.info(f"📊 Found {len(unresolved)} unresolved pairs out of {len(pairs)} total for {organization_id}")
        return unresolved
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about current storage configuration."""
        return {
            "storage_type": "s3" if self.use_s3 else "local",
            "bucket_name": self.bucket_name if self.use_s3 else None,
            "local_path": str(self.local_storage_path) if not self.use_s3 else None,
            "aws_region": self.aws_region if self.use_s3 else None
        }
    
    def store_organization_metadata(self, organization_id: str, metadata: Dict[str, Any]) -> bool:
        """Store organization metadata (document counts, ingestion info, etc.)."""
        try:
            # Add standard fields
            data = {
                "organization_id": organization_id,
                "last_updated": datetime.utcnow().isoformat(),
                **metadata
            }
            
            json_data = json.dumps(data, indent=2)
            
            if self.use_s3:
                # Store in S3
                key = self._get_metadata_file_path(organization_id)
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=json_data,
                    ContentType='application/json'
                )
                logger.info(f"☁️ Stored metadata for {organization_id} in S3")
            else:
                # Store locally
                file_path = self._get_local_metadata_file_path(organization_id)
                with open(file_path, 'w') as f:
                    f.write(json_data)
                logger.info(f"📁 Stored metadata for {organization_id} locally")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store metadata: {e}")
            return False
    
    def get_organization_metadata(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve organization metadata."""
        try:
            if self.use_s3:
                # Get from S3
                key = self._get_metadata_file_path(organization_id)
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                json_data = response['Body'].read().decode('utf-8')
                logger.info(f"☁️ Retrieved metadata for {organization_id} from S3")
            else:
                # Get from local storage
                file_path = self._get_local_metadata_file_path(organization_id)
                if not file_path.exists():
                    logger.info(f"📁 No metadata found for {organization_id}")
                    return None
                
                with open(file_path, 'r') as f:
                    json_data = f.read()
                logger.info(f"📁 Retrieved metadata for {organization_id} from local storage")
            
            return json.loads(json_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve metadata: {e}")
            return None
    
    def update_organization_metadata(self, organization_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in organization metadata."""
        try:
            # Get existing metadata
            existing = self.get_organization_metadata(organization_id)
            if existing:
                existing.update(updates)
                existing["last_updated"] = datetime.utcnow().isoformat()
                return self.store_organization_metadata(organization_id, existing)
            else:
                # Create new metadata
                return self.store_organization_metadata(organization_id, updates)
                
        except Exception as e:
            logger.error(f"❌ Failed to update metadata: {e}")
            return False
    
    def delete_organization_data(self, organization_id: str) -> bool:
        """Delete ALL data for an organization (metadata + duplicate pairs)."""
        try:
            success = True
            
            if self.use_s3:
                # Delete from S3
                try:
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=self._get_file_path(organization_id))
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=self._get_metadata_file_path(organization_id))
                    logger.info(f"☁️ Deleted all data for {organization_id} from S3")
                except Exception as e:
                    logger.warning(f"⚠️ Some S3 deletions failed: {e}")
                    success = False
            else:
                # Delete from local storage
                try:
                    dup_file = self._get_local_file_path(organization_id)
                    meta_file = self._get_local_metadata_file_path(organization_id)
                    
                    if dup_file.exists():
                        dup_file.unlink()
                    if meta_file.exists():
                        meta_file.unlink()
                        
                    # Remove empty directories
                    for path in [dup_file.parent, meta_file.parent]:
                        try:
                            if path.exists() and not any(path.iterdir()):
                                path.rmdir()
                        except:
                            pass
                            
                    logger.info(f"📁 Deleted all data for {organization_id} from local storage")
                except Exception as e:
                    logger.warning(f"⚠️ Some local deletions failed: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to delete organization data: {e}")
            return False
