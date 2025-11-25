"""
Data Transfer Cost Analyzer Service
Identifies expensive data transfer patterns and optimization opportunities
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataTransferRecommendation:
    """Recommendation for data transfer optimization"""
    source: str  # Service or region
    destination: str  # Service or region
    transfer_type: str  # "INTER_REGION", "INTERNET_OUT", "INTER_AZ", "CLOUDFRONT"
    monthly_gb: float
    current_cost_monthly: float
    recommended_solution: str
    estimated_savings_monthly: float
    estimated_savings_annual: float
    estimated_savings_percentage: float
    priority: str
    risk_level: str
    implementation_effort: str  # "LOW", "MEDIUM", "HIGH"


class DataTransferAnalyzer:
    """Analyzes data transfer costs and optimization opportunities"""
    
    # Data transfer pricing (us-east-1, per GB)
    TRANSFER_PRICING = {
        'INTER_REGION': 0.02,  # Between regions
        'INTERNET_OUT_FIRST_10TB': 0.09,  # First 10 TB/month
        'INTERNET_OUT_NEXT_40TB': 0.085,  # Next 40 TB/month
        'INTERNET_OUT_NEXT_100TB': 0.07,  # Next 100 TB/month
        'INTER_AZ': 0.01,  # Between AZs
        'CLOUDFRONT_TO_INTERNET': 0.085,  # CloudFront to internet
        'S3_TO_CLOUDFRONT': 0.00  # Free
    }
    
    def __init__(self, ce_client, cloudwatch_client):
        """
        Initialize Data Transfer Analyzer
        
        Args:
            ce_client: AWS Cost Explorer client
            cloudwatch_client: AWS CloudWatch client
        """
        self.ce_client = ce_client
        self.cloudwatch_client = cloudwatch_client
    
    def analyze_data_transfer_costs(
        self,
        period_days: int = 30,
        min_cost_monthly: float = 10.0
    ) -> List[DataTransferRecommendation]:
        """
        Analyze data transfer costs and find optimization opportunities
        
        Args:
            period_days: Historical period to analyze
            min_cost_monthly: Minimum cost to generate recommendation
            
        Returns:
            List of data transfer recommendations
        """
        logger.info("Analyzing data transfer costs...")
        
        try:
            # Get data transfer costs from Cost Explorer
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_days)
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.isoformat(),
                    'End': end_date.isoformat()
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'USAGE_TYPE_GROUP',
                        'Values': ['EC2: Data Transfer', 'S3: Data Transfer']
                    }
                }
            )
            
            recommendations = []
            
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    usage_type = group.get('Keys', [''])[0]
                    cost = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', 0))
                    usage_gb = float(group.get('Metrics', {}).get('UsageQuantity', {}).get('Amount', 0))
                    
                    # Normalize to monthly cost
                    days_in_period = (end_date - start_date).days
                    monthly_cost = cost * (30 / days_in_period) if days_in_period > 0 else cost
                    monthly_gb = usage_gb * (30 / days_in_period) if days_in_period > 0 else usage_gb
                    
                    if monthly_cost < min_cost_monthly:
                        continue
                    
                    # Analyze usage type and generate recommendation
                    rec = self._analyze_usage_type(usage_type, monthly_gb, monthly_cost)
                    
                    if rec:
                        recommendations.append(rec)
            
            logger.info(f"Found {len(recommendations)} data transfer optimization opportunities")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error analyzing data transfer costs: {e}")
            return []
    
    def _analyze_usage_type(
        self,
        usage_type: str,
        monthly_gb: float,
        monthly_cost: float
    ) -> Optional[DataTransferRecommendation]:
        """Analyze specific usage type and generate recommendation"""
        
        # Inter-Region Data Transfer
        if 'DataTransfer-Regional' in usage_type or 'InterRegion' in usage_type:
            return DataTransferRecommendation(
                source="Region A",
                destination="Region B",
                transfer_type="INTER_REGION",
                monthly_gb=monthly_gb,
                current_cost_monthly=monthly_cost,
                recommended_solution="Use S3 Transfer Acceleration or consolidate resources in same region",
                estimated_savings_monthly=monthly_cost * 0.5,  # 50% reduction
                estimated_savings_annual=monthly_cost * 0.5 * 12,
                estimated_savings_percentage=50.0,
                priority="HIGH" if monthly_cost > 100 else "MEDIUM",
                risk_level="LOW",
                implementation_effort="MEDIUM"
            )
        
        # Internet Egress (Data Out)
        if 'DataTransfer-Out' in usage_type or 'Bytes-Out' in usage_type:
            # Recommend CloudFront
            cloudfront_cost = monthly_gb * self.TRANSFER_PRICING['CLOUDFRONT_TO_INTERNET']
            savings = monthly_cost - cloudfront_cost
            savings_pct = (savings / monthly_cost * 100) if monthly_cost > 0 else 0
            
            if savings_pct > 10:
                return DataTransferRecommendation(
                    source="S3 or EC2",
                    destination="Internet",
                    transfer_type="INTERNET_OUT",
                    monthly_gb=monthly_gb,
                    current_cost_monthly=monthly_cost,
                    recommended_solution="Use CloudFront CDN to reduce data transfer costs",
                    estimated_savings_monthly=savings,
                    estimated_savings_annual=savings * 12,
                    estimated_savings_percentage=savings_pct,
                    priority="HIGH" if monthly_cost > 200 else "MEDIUM",
                    risk_level="LOW",
                    implementation_effort="LOW"
                )
        
        # Inter-AZ Data Transfer
        if 'DataTransfer-In' in usage_type or 'InterZone' in usage_type:
            return DataTransferRecommendation(
                source="AZ A",
                destination="AZ B",
                transfer_type="INTER_AZ",
                monthly_gb=monthly_gb,
                current_cost_monthly=monthly_cost,
                recommended_solution="Consolidate resources in same AZ or use VPC endpoints",
                estimated_savings_monthly=monthly_cost * 0.7,  # 70% reduction
                estimated_savings_annual=monthly_cost * 0.7 * 12,
                estimated_savings_percentage=70.0,
                priority="MEDIUM",
                risk_level="MEDIUM",  # May impact availability
                implementation_effort="HIGH"
            )
        
        return None
    
    def _get_bucket_metrics(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket metrics including size, objects, age, access pattern"""
        try:
            # Get bucket size and object count
            # Note: In production, use S3 Storage Lens or CloudWatch metrics
            
            # Simplified metrics (placeholder)
            metrics = {
                'storage_class': 'STANDARD',
                'size_gb': 500.0,
                'objects_count': 50000,
                'average_age_days': 90,
                'access_pattern': 'INFREQUENT'  # Would analyze CloudWatch GetObject metrics
            }
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error getting metrics for bucket {bucket_name}: {e}")
            return {}
