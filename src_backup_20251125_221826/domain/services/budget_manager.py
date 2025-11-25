"""
Budget Manager Service
Creates and manages AWS Budgets based on FinOps recommendations
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BudgetAlert:
    """Budget alert configuration"""
    budget_name: str
    budget_amount: float
    alert_threshold_percentage: float  # e.g., 80.0 for 80%
    notification_email: str
    budget_type: str  # "COST", "USAGE"
    time_unit: str  # "MONTHLY", "QUARTERLY", "ANNUALLY"


class BudgetManager:
    """Manages AWS Budgets and alerts"""
    
    def __init__(self, budgets_client, sns_client):
        """
        Initialize Budget Manager
        
        Args:
            budgets_client: AWS Budgets client
            sns_client: AWS SNS client
        """
        self.budgets_client = budgets_client
        self.sns_client = sns_client
    
    def create_budget_from_forecast(
        self,
        budget_name: str,
        forecasted_monthly_cost: float,
        notification_email: str,
        buffer_percentage: float = 10.0,
        alert_thresholds: List[float] = [80.0, 90.0, 100.0]
    ) -> Dict[str, Any]:
        """
        Create budget based on cost forecast
        
        Args:
            budget_name: Name for the budget
            forecasted_monthly_cost: Forecasted monthly cost
            notification_email: Email for alerts
            buffer_percentage: Buffer above forecast (default 10%)
            alert_thresholds: Alert threshold percentages
            
        Returns:
            Budget creation result
        """
        logger.info(f"Creating budget '{budget_name}' with forecast ${forecasted_monthly_cost:.2f}")
        
        try:
            # Add buffer to forecast
            budget_amount = forecasted_monthly_cost * (1 + buffer_percentage / 100)
            
            # Create SNS topic for notifications
            topic_arn = self._create_sns_topic(budget_name, notification_email)
            
            # Create budget
            budget = {
                'BudgetName': budget_name,
                'BudgetLimit': {
                    'Amount': str(budget_amount),
                    'Unit': 'USD'
                },
                'TimeUnit': 'MONTHLY',
                'BudgetType': 'COST',
                'CostTypes': {
                    'IncludeTax': True,
                    'IncludeSubscription': True,
                    'UseBlended': False,
                    'IncludeRefund': False,
                    'IncludeCredit': False,
                    'IncludeUpfront': True,
                    'IncludeRecurring': True,
                    'IncludeOtherSubscription': True,
                    'IncludeSupport': True,
                    'IncludeDiscount': True,
                    'UseAmortized': False
                }
            }
            
            # Create notifications for each threshold
            notifications = []
            for threshold in alert_thresholds:
                notification = {
                    'NotificationType': 'ACTUAL',
                    'ComparisonOperator': 'GREATER_THAN',
                    'Threshold': threshold,
                    'ThresholdType': 'PERCENTAGE',
                    'NotificationState': 'ALARM'
                }
                
                subscriber = {
                    'SubscriptionType': 'SNS',
                    'Address': topic_arn
                }
                
                notifications.append({
                    'Notification': notification,
                    'Subscribers': [subscriber]
                })
            
            # Create budget with notifications
            response = self.budgets_client.create_budget(
                AccountId=self._get_account_id(),
                Budget=budget,
                NotificationsWithSubscribers=notifications
            )
            
            logger.info(f"Budget '{budget_name}' created successfully")
            
            return {
                'budget_name': budget_name,
                'budget_amount': budget_amount,
                'forecasted_cost': forecasted_monthly_cost,
                'buffer_percentage': buffer_percentage,
                'topic_arn': topic_arn,
                'alert_thresholds': alert_thresholds,
                'status': 'CREATED'
            }
            
        except Exception as e:
            logger.error(f"Error creating budget: {e}")
            return {
                'budget_name': budget_name,
                'status': 'FAILED',
                'error': str(e)
            }
    
    def create_service_budget(
        self,
        service_name: str,
        monthly_limit: float,
        notification_email: str
    ) -> Dict[str, Any]:
        """
        Create budget for specific AWS service
        
        Args:
            service_name: AWS service name (e.g., "Amazon EC2")
            monthly_limit: Monthly cost limit
            notification_email: Email for alerts
            
        Returns:
            Budget creation result
        """
        logger.info(f"Creating service budget for {service_name} with limit ${monthly_limit:.2f}")
        
        try:
            budget_name = f"{service_name.replace(' ', '-')}-Monthly-Budget"
            topic_arn = self._create_sns_topic(budget_name, notification_email)
            
            budget = {
                'BudgetName': budget_name,
                'BudgetLimit': {
                    'Amount': str(monthly_limit),
                    'Unit': 'USD'
                },
                'TimeUnit': 'MONTHLY',
                'BudgetType': 'COST',
                'CostFilters': {
                    'Service': [service_name]
                },
                'CostTypes': {
                    'IncludeTax': True,
                    'IncludeSubscription': True,
                    'UseBlended': False
                }
            }
            
            notification = {
                'Notification': {
                    'NotificationType': 'FORECASTED',
                    'ComparisonOperator': 'GREATER_THAN',
                    'Threshold': 100.0,
                    'ThresholdType': 'PERCENTAGE',
                    'NotificationState': 'ALARM'
                },
                'Subscribers': [{
                    'SubscriptionType': 'SNS',
                    'Address': topic_arn
                }]
            }
            
            response = self.budgets_client.create_budget(
                AccountId=self._get_account_id(),
                Budget=budget,
                NotificationsWithSubscribers=[notification]
            )
            
            logger.info(f"Service budget for {service_name} created successfully")
            
            return {
                'budget_name': budget_name,
                'service': service_name,
                'monthly_limit': monthly_limit,
                'topic_arn': topic_arn,
                'status': 'CREATED'
            }
            
        except Exception as e:
            logger.error(f"Error creating service budget: {e}")
            return {
                'budget_name': budget_name,
                'status': 'FAILED',
                'error': str(e)
            }
    
    def _create_sns_topic(self, budget_name: str, email: str) -> str:
        """Create SNS topic for budget notifications"""
        try:
            topic_name = f"finops-budget-{budget_name}"
            
            # Create topic
            response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            
            # Subscribe email
            self.sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email
            )
            
            logger.info(f"SNS topic created: {topic_arn}")
            return topic_arn
            
        except Exception as e:
            logger.warning(f"Error creating SNS topic: {e}")
            return ""
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        import boto3
        sts = boto3.client('sts')
        return sts.get_caller_identity()['Account']
