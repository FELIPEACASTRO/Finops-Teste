"""
AWS implementation of cost repository.
Handles cost data collection from AWS Cost Explorer.
"""

import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from decimal import Decimal

from ...domain.entities import CostData
from ...domain.repositories.resource_repository import ICostRepository


class AWSCostRepository(ICostRepository):
    """
    AWS implementation of cost repository using Cost Explorer API.
    
    Follows the Repository Pattern and Adapter Pattern.
    """

    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.logger = logging.getLogger(__name__)
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Cost Explorer client (Singleton pattern)."""
        if self._client is None:
            self._client = boto3.client('ce', region_name=self.region)
        return self._client

    async def get_cost_data(self, start_date: datetime, end_date: datetime) -> CostData:
        """
        Get comprehensive cost data for the specified period.
        
        Time Complexity: O(1) - single API call
        Space Complexity: O(d) where d is number of days
        """
        try:
            # Format dates for Cost Explorer API
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            period_days = (end_date - start_date).days

            # Get total cost
            total_cost_response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_str,
                    'End': end_str
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost']
            )

            # Calculate total cost
            total_cost = Decimal('0')
            daily_costs = []
            
            for result in total_cost_response['ResultsByTime']:
                period_cost = Decimal(result['Total']['BlendedCost']['Amount'])
                total_cost += period_cost
                
                daily_costs.append({
                    'date': result['TimePeriod']['Start'],
                    'cost_usd': float(period_cost)
                })

            # Get cost by service
            service_cost_response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_str,
                    'End': end_str
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )

            # Parse service costs
            cost_by_service = {}
            for result in service_cost_response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    service_cost = Decimal(group['Metrics']['BlendedCost']['Amount'])
                    
                    if service_name in cost_by_service:
                        cost_by_service[service_name] += service_cost
                    else:
                        cost_by_service[service_name] = service_cost

            return CostData(
                total_cost_usd=total_cost,
                period_days=period_days,
                cost_by_service=cost_by_service,
                daily_costs=daily_costs
            )

        except Exception as e:
            self.logger.error(f"Failed to get cost data: {str(e)}")
            # Return empty cost data on error
            return CostData(
                total_cost_usd=Decimal('0'),
                period_days=(end_date - start_date).days,
                cost_by_service={},
                daily_costs=[]
            )

    async def get_cost_by_service(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, float]:
        """
        Get costs broken down by AWS service.
        
        Time Complexity: O(s) where s is number of services
        Space Complexity: O(s)
        """
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_str,
                    'End': end_str
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )

            service_costs = {}
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    service_cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if service_name in service_costs:
                        service_costs[service_name] += service_cost
                    else:
                        service_costs[service_name] = service_cost

            return service_costs

        except Exception as e:
            self.logger.error(f"Failed to get cost by service: {str(e)}")
            return {}

    async def get_resource_cost(
        self, 
        resource_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """
        Get cost for a specific resource.
        
        Note: This is challenging with Cost Explorer as it doesn't directly
        support resource-level cost attribution. This is a simplified implementation.
        """
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            # Try to get cost using resource tags if available
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_str,
                    'End': end_str
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'TAG',
                        'Key': 'ResourceId'
                    }
                ]
            )

            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    if resource_id in group['Keys'][0]:
                        return float(group['Metrics']['BlendedCost']['Amount'])

            # If not found, return 0
            return 0.0

        except Exception as e:
            self.logger.error(f"Failed to get cost for resource {resource_id}: {str(e)}")
            return 0.0

    async def get_cost_forecast(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, float]:
        """
        Get cost forecast for the specified period.
        
        Time Complexity: O(1)
        Space Complexity: O(d) where d is number of forecast days
        """
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            response = self.client.get_cost_forecast(
                TimePeriod={
                    'Start': start_str,
                    'End': end_str
                },
                Metric='BLENDED_COST',
                Granularity='MONTHLY'
            )

            forecast_data = {}
            for result in response['ForecastResultsByTime']:
                period = result['TimePeriod']['Start']
                mean_value = float(result['MeanValue'])
                
                forecast_data[period] = {
                    'mean_cost': mean_value,
                    'prediction_interval_lower': float(result.get('PredictionIntervalLowerBound', mean_value * 0.9)),
                    'prediction_interval_upper': float(result.get('PredictionIntervalUpperBound', mean_value * 1.1))
                }

            return forecast_data

        except Exception as e:
            self.logger.error(f"Failed to get cost forecast: {str(e)}")
            return {}

    async def get_rightsizing_recommendations(self) -> List[Dict[str, any]]:
        """
        Get AWS rightsizing recommendations.
        
        Time Complexity: O(r) where r is number of recommendations
        Space Complexity: O(r)
        """
        try:
            response = self.client.get_rightsizing_recommendation(
                Service='AmazonEC2'
            )

            recommendations = []
            for rec in response.get('RightsizingRecommendations', []):
                recommendations.append({
                    'resource_id': rec.get('ResourceId'),
                    'current_instance': rec.get('CurrentInstance', {}).get('InstanceType'),
                    'recommended_instance': rec.get('RightsizingType'),
                    'estimated_monthly_savings': float(rec.get('EstimatedMonthlySavings', {}).get('Amount', 0)),
                    'finding': rec.get('Finding'),
                    'finding_reason_codes': rec.get('FindingReasonCodes', [])
                })

            return recommendations

        except Exception as e:
            self.logger.error(f"Failed to get rightsizing recommendations: {str(e)}")
            return []

    async def get_cost_anomalies(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, any]]:
        """
        Get cost anomalies for the specified period.
        
        Time Complexity: O(a) where a is number of anomalies
        Space Complexity: O(a)
        """
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            response = self.client.get_anomalies(
                DateInterval={
                    'StartDate': start_str,
                    'EndDate': end_str
                }
            )

            anomalies = []
            for anomaly in response.get('Anomalies', []):
                anomalies.append({
                    'anomaly_id': anomaly.get('AnomalyId'),
                    'anomaly_score': anomaly.get('AnomalyScore', {}).get('CurrentScore'),
                    'impact': float(anomaly.get('Impact', {}).get('TotalImpact', 0)),
                    'service': anomaly.get('DimensionKey'),
                    'start_date': anomaly.get('AnomalyStartDate'),
                    'end_date': anomaly.get('AnomalyEndDate'),
                    'feedback': anomaly.get('Feedback')
                })

            return anomalies

        except Exception as e:
            self.logger.error(f"Failed to get cost anomalies: {str(e)}")
            return []