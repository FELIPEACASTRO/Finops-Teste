"""
S3 implementation of report repository.
Handles saving and retrieving analysis reports from S3.
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError

from ...domain.repositories.resource_repository import IReportRepository


class S3ReportRepository(IReportRepository):
    """
    S3 implementation of report repository.
    
    Follows the Repository Pattern and provides reliable report persistence.
    """

    def __init__(self, bucket_name: str, region: str = 'us-east-1', prefix: str = 'finops-reports/'):
        self.bucket_name = bucket_name
        self.region = region
        self.prefix = prefix
        self.logger = logging.getLogger(__name__)
        
        # Initialize S3 client (Singleton pattern)
        self._s3_client = None

    @property
    def s3_client(self):
        """Lazy initialization of S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client('s3', region_name=self.region)
        return self._s3_client

    async def save_report(self, report: Dict[str, Any], report_id: str) -> str:
        """
        Save analysis report to S3.
        
        Time Complexity: O(1) - single S3 PUT operation
        Space Complexity: O(r) where r is report size
        
        Args:
            report: Report data dictionary
            report_id: Unique identifier for the report
            
        Returns:
            str: S3 location of saved report
            
        Raises:
            Exception: If save operation fails
        """
        try:
            # Create S3 key with timestamp and report ID
            timestamp = datetime.utcnow().strftime('%Y/%m/%d')
            s3_key = f"{self.prefix}{timestamp}/{report_id}.json"
            
            # Add metadata
            report_with_metadata = {
                **report,
                "metadata": {
                    "report_id": report_id,
                    "saved_at": datetime.utcnow().isoformat(),
                    "s3_location": f"s3://{self.bucket_name}/{s3_key}",
                    "version": "4.0.0"
                }
            }
            
            # Convert to JSON
            report_json = json.dumps(report_with_metadata, indent=2, default=str)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=report_json,
                ContentType='application/json',
                Metadata={
                    'report-id': report_id,
                    'generated-at': report.get('generated_at', ''),
                    'total-resources': str(report.get('total_resources_analyzed', 0)),
                    'total-savings': str(report.get('total_monthly_savings_usd', 0))
                },
                ServerSideEncryption='AES256'  # Encrypt at rest
            )
            
            s3_location = f"s3://{self.bucket_name}/{s3_key}"
            self.logger.info(f"Report saved successfully to {s3_location}")
            
            return s3_location
            
        except Exception as e:
            self.logger.error(f"Failed to save report {report_id}: {str(e)}")
            raise

    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a saved report by ID.
        
        Time Complexity: O(1) - single S3 GET operation
        Space Complexity: O(r) where r is report size
        """
        try:
            # Search for report across date partitions (last 30 days)
            for days_back in range(30):
                date = datetime.utcnow() - timedelta(days=days_back)
                timestamp = date.strftime('%Y/%m/%d')
                s3_key = f"{self.prefix}{timestamp}/{report_id}.json"
                
                try:
                    response = self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=s3_key
                    )
                    
                    # Parse JSON content
                    report_data = json.loads(response['Body'].read())
                    
                    self.logger.info(f"Report {report_id} retrieved successfully")
                    return report_data
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        continue  # Try next date
                    else:
                        raise
            
            # Report not found
            self.logger.warning(f"Report {report_id} not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get report {report_id}: {str(e)}")
            return None

    async def list_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent reports.
        
        Time Complexity: O(n) where n is number of objects to scan
        Space Complexity: O(l) where l is limit
        """
        try:
            reports = []
            
            # List objects with pagination
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=self.prefix,
                MaxKeys=100
            )
            
            for page in page_iterator:
                if 'Contents' not in page:
                    continue
                
                # Sort by last modified (newest first)
                objects = sorted(
                    page['Contents'], 
                    key=lambda x: x['LastModified'], 
                    reverse=True
                )
                
                for obj in objects:
                    if len(reports) >= limit:
                        break
                    
                    # Extract report info from metadata
                    try:
                        # Get object metadata
                        head_response = self.s3_client.head_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        
                        metadata = head_response.get('Metadata', {})
                        
                        report_info = {
                            'report_id': metadata.get('report-id', 'unknown'),
                            's3_location': f"s3://{self.bucket_name}/{obj['Key']}",
                            'size_bytes': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat(),
                            'generated_at': metadata.get('generated-at', ''),
                            'total_resources': int(metadata.get('total-resources', 0)),
                            'total_savings': float(metadata.get('total-savings', 0))
                        }
                        
                        reports.append(report_info)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to get metadata for {obj['Key']}: {str(e)}")
                        continue
                
                if len(reports) >= limit:
                    break
            
            return reports
            
        except Exception as e:
            self.logger.error(f"Failed to list reports: {str(e)}")
            return []

    async def delete_report(self, report_id: str) -> bool:
        """
        Delete a report by ID.
        
        Time Complexity: O(1) - single S3 DELETE operation
        Space Complexity: O(1)
        """
        try:
            # Search for report to delete
            for days_back in range(30):
                date = datetime.utcnow() - timedelta(days=days_back)
                timestamp = date.strftime('%Y/%m/%d')
                s3_key = f"{self.prefix}{timestamp}/{report_id}.json"
                
                try:
                    # Check if object exists
                    self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=s3_key
                    )
                    
                    # Delete the object
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=s3_key
                    )
                    
                    self.logger.info(f"Report {report_id} deleted successfully")
                    return True
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        continue  # Try next date
                    else:
                        raise
            
            # Report not found
            self.logger.warning(f"Report {report_id} not found for deletion")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete report {report_id}: {str(e)}")
            return False

    async def cleanup_old_reports(self, days_to_keep: int = 90) -> int:
        """
        Clean up reports older than specified days.
        
        Time Complexity: O(n) where n is number of objects
        Space Complexity: O(b) where b is batch size
        
        Returns:
            int: Number of reports deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            # List all objects
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )
            
            objects_to_delete = []
            
            for page in page_iterator:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        objects_to_delete.append({'Key': obj['Key']})
                        
                        # Delete in batches of 1000 (S3 limit)
                        if len(objects_to_delete) >= 1000:
                            response = self.s3_client.delete_objects(
                                Bucket=self.bucket_name,
                                Delete={'Objects': objects_to_delete}
                            )
                            deleted_count += len(response.get('Deleted', []))
                            objects_to_delete = []
            
            # Delete remaining objects
            if objects_to_delete:
                response = self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                deleted_count += len(response.get('Deleted', []))
            
            self.logger.info(f"Cleaned up {deleted_count} old reports")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old reports: {str(e)}")
            return 0

    def ensure_bucket_exists(self) -> bool:
        """
        Ensure S3 bucket exists and is properly configured.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"S3 bucket {self.bucket_name} exists")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404':
                self.logger.error(f"S3 bucket {self.bucket_name} does not exist")
                return False
            elif error_code == '403':
                self.logger.error(f"No permission to access S3 bucket {self.bucket_name}")
                return False
            else:
                self.logger.error(f"Error checking S3 bucket: {str(e)}")
                return False