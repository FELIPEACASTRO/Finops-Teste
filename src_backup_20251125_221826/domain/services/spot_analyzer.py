"""
Spot Instance Analyzer Service
Identifies opportunities to migrate to Spot Instances
"""
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SpotRecommendation:
    """Recommendation for Spot Instance migration"""
    instance_id: str
    instance_type: str
    region: str
    availability_zone: str
    current_cost_monthly: float
    spot_cost_monthly: float
    estimated_savings_monthly: float
    estimated_savings_annual: float
    estimated_savings_percentage: float
    interruption_rate: str  # "<5%", "5-10%", "10-15%", "15-20%", ">20%"
    workload_suitability: str  # "EXCELLENT", "GOOD", "FAIR", "POOR"
    risk_level: str
    priority: str
    migration_strategy: str  # "FULL_SPOT", "MIXED_FLEET", "SPOT_FLEET"


class SpotAnalyzer:
    """Analyzes Spot Instance opportunities"""
    
    def __init__(self, ec2_client, ce_client):
        """
        Initialize Spot Analyzer
        
        Args:
            ec2_client: AWS EC2 client
            ce_client: AWS Cost Explorer client
        """
        self.ec2_client = ec2_client
        self.ce_client = ce_client
        
    def analyze_spot_opportunities(
        self,
        instances: List[Dict[str, Any]],
        region: str
    ) -> List[SpotRecommendation]:
        """
        Analyze which EC2 instances are good candidates for Spot
        
        Args:
            instances: List of EC2 instance data
            region: AWS region
            
        Returns:
            List of Spot recommendations
        """
        logger.info(f"Analyzing Spot opportunities for {len(instances)} instances in {region}")
        
        recommendations = []
        
        for instance in instances:
            instance_id = instance.get('InstanceId')
            instance_type = instance.get('InstanceType')
            az = instance.get('Placement', {}).get('AvailabilityZone', region + 'a')
            
            # Get Spot pricing
            spot_price = self._get_spot_price(instance_type, az)
            on_demand_price = self._get_on_demand_price(instance_type, region)
            
            if not spot_price or not on_demand_price:
                continue
            
            # Calculate savings
            hours_per_month = 730
            spot_cost_monthly = spot_price * hours_per_month
            on_demand_cost_monthly = on_demand_price * hours_per_month
            savings_monthly = on_demand_cost_monthly - spot_cost_monthly
            savings_annual = savings_monthly * 12
            savings_percentage = (savings_monthly / on_demand_cost_monthly * 100) if on_demand_cost_monthly > 0 else 0
            
            # Get interruption rate
            interruption_rate = self._get_interruption_rate(instance_type, az)
            
            # Determine workload suitability
            workload_suitability = self._assess_workload_suitability(instance, interruption_rate)
            
            # Determine risk and priority
            if workload_suitability == "EXCELLENT" and savings_percentage > 60:
                risk_level = "LOW"
                priority = "HIGH"
            elif workload_suitability in ["EXCELLENT", "GOOD"] and savings_percentage > 50:
                risk_level = "MEDIUM"
                priority = "MEDIUM"
            else:
                risk_level = "HIGH"
                priority = "LOW"
            
            # Determine migration strategy
            if workload_suitability == "EXCELLENT":
                migration_strategy = "FULL_SPOT"
            elif workload_suitability == "GOOD":
                migration_strategy = "MIXED_FLEET"  # 70% Spot, 30% On-Demand
            else:
                migration_strategy = "SPOT_FLEET"  # Use Spot Fleet with fallback
            
            recommendation = SpotRecommendation(
                instance_id=instance_id,
                instance_type=instance_type,
                region=region,
                availability_zone=az,
                current_cost_monthly=on_demand_cost_monthly,
                spot_cost_monthly=spot_cost_monthly,
                estimated_savings_monthly=savings_monthly,
                estimated_savings_annual=savings_annual,
                estimated_savings_percentage=savings_percentage,
                interruption_rate=interruption_rate,
                workload_suitability=workload_suitability,
                risk_level=risk_level,
                priority=priority,
                migration_strategy=migration_strategy
            )
            
            recommendations.append(recommendation)
        
        logger.info(f"Found {len(recommendations)} Spot opportunities")
        return recommendations
    
    def _get_spot_price(self, instance_type: str, az: str) -> Optional[float]:
        """Get current Spot price for instance type"""
        try:
            response = self.ec2_client.describe_spot_price_history(
                InstanceTypes=[instance_type],
                AvailabilityZone=az,
                ProductDescriptions=['Linux/UNIX'],
                MaxResults=1
            )
            
            if response.get('SpotPriceHistory'):
                return float(response['SpotPriceHistory'][0]['SpotPrice'])
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting Spot price for {instance_type}: {e}")
            return None
    
    def _get_on_demand_price(self, instance_type: str, region: str) -> Optional[float]:
        """Get On-Demand price for instance type"""
        # Simplified pricing (in production, use AWS Pricing API)
        pricing_map = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            't3.xlarge': 0.1664,
            't3.2xlarge': 0.3328,
            't3a.micro': 0.0094,
            't3a.small': 0.0188,
            't3a.medium': 0.0376,
            't3a.large': 0.0752,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'm5.2xlarge': 0.384,
            'c5.large': 0.085,
            'c5.xlarge': 0.17,
            'r5.large': 0.126,
            'r5.xlarge': 0.252
        }
        
        return pricing_map.get(instance_type)
    
    def _get_interruption_rate(self, instance_type: str, az: str) -> str:
        """Estimate Spot interruption rate"""
        # Simplified (in production, use historical data)
        # T3/T3a instances typically have very low interruption rates
        if instance_type.startswith('t3'):
            return "<5%"
        elif instance_type.startswith('m5') or instance_type.startswith('c5'):
            return "5-10%"
        else:
            return "10-15%"
    
    def _assess_workload_suitability(self, instance: Dict[str, Any], interruption_rate: str) -> str:
        """Assess if workload is suitable for Spot"""
        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
        
        # Check for fault-tolerant workloads
        workload_type = tags.get('Workload', '').lower()
        
        if any(keyword in workload_type for keyword in ['batch', 'processing', 'analytics', 'dev', 'test']):
            return "EXCELLENT"
        elif any(keyword in workload_type for keyword in ['web', 'api', 'worker']):
            if interruption_rate == "<5%":
                return "GOOD"
            else:
                return "FAIR"
        elif any(keyword in workload_type for keyword in ['database', 'stateful', 'critical']):
            return "POOR"
        else:
            # Unknown workload - conservative assessment
            if interruption_rate == "<5%":
                return "GOOD"
            else:
                return "FAIR"
