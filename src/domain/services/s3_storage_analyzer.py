"""
S3 Storage Class Analyzer Service
Recommends optimal storage classes for S3 buckets
"""
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class S3StorageRecommendation:
    """Recommendation for S3 storage class optimization"""
    bucket_name: str
    current_storage_class: str
    recommended_storage_class: str
    total_size_gb: float
    current_cost_monthly: float
    recommended_cost_monthly: float
    estimated_savings_monthly: float
    estimated_savings_annual: float
    estimated_savings_percentage: float
    access_pattern: str  # "FREQUENT", "INFREQUENT", "ARCHIVE", "UNKNOWN"
    objects_count: int
    average_object_age_days: float
    priority: str
    risk_level: str


class S3StorageAnalyzer:
    """Analyzes S3 storage class optimization opportunities"""
    
    # Storage class pricing (us-east-1, per GB/month)
    STORAGE_PRICING = {
        'STANDARD': 0.023,
        'INTELLIGENT_TIERING': 0.023,  # Same as Standard + $0.0025 monitoring
        'STANDARD_IA': 0.0125,
        'ONEZONE_IA': 0.01,
        'GLACIER_INSTANT_RETRIEVAL': 0.004,
        'GLACIER_FLEXIBLE_RETRIEVAL': 0.0036,
        'GLACIER_DEEP_ARCHIVE': 0.00099
    }
    
    def __init__(self, s3_client, cloudwatch_client):
        """
        Initialize S3 Storage Analyzer
        
        Args:
            s3_client: AWS S3 client
            cloudwatch_client: AWS CloudWatch client
        """
        self.s3_client = s3_client
        self.cloudwatch_client = cloudwatch_client
    
    def analyze_storage_class_opportunities(
        self,
        buckets: List[Dict[str, Any]],
        min_savings_percentage: float = 10.0
    ) -> List[S3StorageRecommendation]:
        """
        Analyze S3 storage class optimization opportunities
        
        Args:
            buckets: List of S3 bucket data
            min_savings_percentage: Minimum savings % to recommend
            
        Returns:
            List of storage class recommendations
        """
        logger.info(f"Analyzing storage class opportunities for {len(buckets)} buckets")
        
        recommendations = []
        
        for bucket in buckets:
            bucket_name = bucket.get('Name')
            
            # Get bucket metrics
            metrics = self._get_bucket_metrics(bucket_name)
            
            if not metrics:
                continue
            
            current_class = metrics.get('storage_class', 'STANDARD')
            size_gb = metrics.get('size_gb', 0)
            objects_count = metrics.get('objects_count', 0)
            avg_age_days = metrics.get('average_age_days', 0)
            access_pattern = metrics.get('access_pattern', 'UNKNOWN')
            
            # Determine recommended storage class
            recommended_class = self._recommend_storage_class(
                access_pattern, avg_age_days, size_gb
            )
            
            if recommended_class == current_class:
                continue  # No change needed
            
            # Calculate costs
            current_cost = size_gb * self.STORAGE_PRICING.get(current_class, 0.023)
            recommended_cost = size_gb * self.STORAGE_PRICING.get(recommended_class, 0.023)
            
            # Add monitoring cost for Intelligent-Tiering
            if recommended_class == 'INTELLIGENT_TIERING':
                recommended_cost += size_gb * 0.0025
            
            savings_monthly = current_cost - recommended_cost
            savings_annual = savings_monthly * 12
            savings_percentage = (savings_monthly / current_cost * 100) if current_cost > 0 else 0
            
            if savings_percentage < min_savings_percentage:
                continue
            
            # Determine risk and priority
            if recommended_class == 'INTELLIGENT_TIERING':
                risk_level = "LOW"  # Automatic tiering, no risk
            elif access_pattern == "INFREQUENT" and recommended_class in ['STANDARD_IA', 'ONEZONE_IA']:
                risk_level = "LOW"
            elif access_pattern == "ARCHIVE":
                risk_level = "MEDIUM"  # Retrieval time consideration
            else:
                risk_level = "MEDIUM"
            
            if savings_percentage > 50:
                priority = "HIGH"
            elif savings_percentage > 30:
                priority = "MEDIUM"
            else:
                priority = "LOW"
            
            recommendation = S3StorageRecommendation(
                bucket_name=bucket_name,
                current_storage_class=current_class,
                recommended_storage_class=recommended_class,
                total_size_gb=size_gb,
                current_cost_monthly=current_cost,
                recommended_cost_monthly=recommended_cost,
                estimated_savings_monthly=savings_monthly,
                estimated_savings_annual=savings_annual,
                estimated_savings_percentage=savings_percentage,
                access_pattern=access_pattern,
                objects_count=objects_count,
                average_object_age_days=avg_age_days,
                priority=priority,
                risk_level=risk_level
            )
            
            recommendations.append(recommendation)
        
        logger.info(f"Found {len(recommendations)} S3 storage class opportunities")
        return recommendations
    
    def _get_bucket_metrics(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket size, object count, and access patterns"""
        try:
            # Get bucket size from CloudWatch
            # Note: This is simplified - in production, use S3 Storage Lens or Inventory
            
            # Simulate metrics (in production, query CloudWatch/Storage Lens)
            metrics = {
                'size_gb': 100.0,  # Placeholder
                'objects_count': 10000,  # Placeholder
                'average_age_days': 180,  # Placeholder
                'access_pattern': 'INFREQUENT',  # Placeholder
                'storage_class': 'STANDARD'
            }
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error getting metrics for bucket {bucket_name}: {e}")
            return {}
    
    def _recommend_storage_class(
        self,
        access_pattern: str,
        avg_age_days: float,
        size_gb: float
    ) -> str:
        """
        Recommend optimal storage class based on access pattern
        
        Args:
            access_pattern: Access pattern (FREQUENT, INFREQUENT, ARCHIVE, UNKNOWN)
            avg_age_days: Average age of objects in days
            size_gb: Total size in GB
            
        Returns:
            Recommended storage class
        """
        # For unknown patterns, recommend Intelligent-Tiering (automatic optimization)
        if access_pattern == "UNKNOWN":
            return "INTELLIGENT_TIERING"
        
        # Frequent access - keep in Standard
        if access_pattern == "FREQUENT":
            return "STANDARD"
        
        # Infrequent access
        if access_pattern == "INFREQUENT":
            if avg_age_days < 30:
                return "STANDARD"  # Too new for IA
            elif size_gb > 1000:  # Large buckets benefit from Intelligent-Tiering
                return "INTELLIGENT_TIERING"
            else:
                return "STANDARD_IA"
        
        # Archive
        if access_pattern == "ARCHIVE":
            if avg_age_days > 180:
                return "GLACIER_DEEP_ARCHIVE"  # Very old data
            elif avg_age_days > 90:
                return "GLACIER_FLEXIBLE_RETRIEVAL"
            else:
                return "GLACIER_INSTANT_RETRIEVAL"
        
        # Default to Intelligent-Tiering for safety
        return "INTELLIGENT_TIERING"
