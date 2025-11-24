"""
AWS Lambda handler for FinOps analysis.
Entry point for the application following Clean Architecture.
"""

import json
import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, Any

from ..application.use_cases.analyze_resources_use_case import (
    AnalyzeResourcesUseCase, 
    AnalyzeResourcesCommand
)
from ..infrastructure.aws.resource_repository import AWSResourceRepository
from ..infrastructure.aws.cost_repository import AWSCostRepository
from ..infrastructure.aws.s3_report_repository import S3ReportRepository
from ..infrastructure.ai.bedrock_analysis_service import BedrockAnalysisService
from ..core.config import Config
from ..core.logger import setup_logger


class LambdaController:
    """
    Lambda controller following the Controller Pattern.
    
    Orchestrates the application flow and handles AWS Lambda integration.
    Follows Dependency Injection and Single Responsibility principles.
    """

    def __init__(self):
        # Setup logging
        self.logger = setup_logger(__name__)
        
        # Load configuration
        self.config = Config()
        
        # Initialize repositories and services (Dependency Injection)
        self.resource_repository = AWSResourceRepository(region=self.config.aws_region)
        self.cost_repository = AWSCostRepository(region=self.config.aws_region)
        self.report_repository = S3ReportRepository(
            bucket_name=self.config.s3_bucket_name,
            region=self.config.aws_region
        )
        self.analysis_service = BedrockAnalysisService(
            model_id=self.config.bedrock_model_id,
            region=self.config.aws_region
        )
        
        # Initialize use case
        self.analyze_resources_use_case = AnalyzeResourcesUseCase(
            resource_repository=self.resource_repository,
            cost_repository=self.cost_repository,
            report_repository=self.report_repository,
            analysis_service=self.analysis_service,
            logger=self.logger
        )

    async def handle_analysis_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle analysis request from Lambda event.
        
        Time Complexity: O(n * m) where n is resources and m is analysis complexity
        Space Complexity: O(n)
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info("Starting FinOps analysis")
            
            # Parse event parameters
            regions = event.get('regions', [self.config.aws_region])
            analysis_period_days = event.get('analysis_period_days', self.config.historical_days)
            include_cost_data = event.get('include_cost_data', True)
            save_report = event.get('save_report', True)
            
            # Validate regions
            if not regions:
                regions = [self.config.aws_region]
            
            # Create command
            command = AnalyzeResourcesCommand(
                regions=regions,
                analysis_period_days=analysis_period_days,
                include_cost_data=include_cost_data,
                save_report=save_report
            )
            
            # Execute analysis
            result = await self.analyze_resources_use_case.execute(command)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Prepare response
            response = {
                "statusCode": 200 if result.success else 500,
                "body": {
                    **result.to_dict(),
                    "execution_time_seconds": execution_time
                }
            }
            
            if result.success:
                self.logger.info(f"Analysis completed successfully in {execution_time:.2f} seconds")
                
                # Send notification if configured
                if self.config.email_to and result.report:
                    await self._send_notification(result.report.to_dict(), result.report_location)
            else:
                self.logger.error(f"Analysis failed: {result.error_message}")
            
            return response
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(f"Unexpected error in analysis: {str(e)}")
            
            return {
                "statusCode": 500,
                "body": {
                    "success": False,
                    "error_message": str(e),
                    "execution_time_seconds": execution_time
                }
            }

    async def handle_report_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report retrieval request."""
        try:
            report_id = event.get('report_id')
            if not report_id:
                return {
                    "statusCode": 400,
                    "body": {"error": "report_id is required"}
                }
            
            report = await self.report_repository.get_report(report_id)
            
            if report:
                return {
                    "statusCode": 200,
                    "body": {"report": report}
                }
            else:
                return {
                    "statusCode": 404,
                    "body": {"error": "Report not found"}
                }
                
        except Exception as e:
            self.logger.error(f"Error retrieving report: {str(e)}")
            return {
                "statusCode": 500,
                "body": {"error": str(e)}
            }

    async def handle_list_reports_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list reports request."""
        try:
            limit = event.get('limit', 10)
            reports = await self.report_repository.list_reports(limit)
            
            return {
                "statusCode": 200,
                "body": {"reports": reports}
            }
            
        except Exception as e:
            self.logger.error(f"Error listing reports: {str(e)}")
            return {
                "statusCode": 500,
                "body": {"error": str(e)}
            }

    async def _send_notification(self, report_data: Dict[str, Any], report_location: str) -> None:
        """Send email notification with analysis results."""
        try:
            if not self.config.email_from or not self.config.email_to:
                self.logger.info("Email notification not configured, skipping")
                return
            
            # Import SES client here to avoid circular imports
            import boto3
            
            ses_client = boto3.client('ses', region_name=self.config.aws_region)
            
            # Prepare email content
            subject = f"FinOps Analysis Report - {report_data.get('generated_at', 'Unknown')}"
            
            # Create summary
            summary = report_data.get('bedrock_analysis', {}).get('summary', {})
            total_savings = summary.get('total_monthly_savings_usd', 0)
            high_priority = summary.get('high_priority_actions', 0)
            
            body_text = f"""
FinOps Analysis Report

Analysis Summary:
- Total Resources Analyzed: {report_data.get('resources_collected', 0)}
- Potential Monthly Savings: ${total_savings:,.2f}
- High Priority Actions: {high_priority}

Report Location: {report_location}

Generated at: {report_data.get('generated_at', 'Unknown')}
Model Used: {report_data.get('model_used', 'Unknown')}
"""
            
            body_html = f"""
<html>
<head></head>
<body>
    <h2>FinOps Analysis Report</h2>
    
    <h3>Analysis Summary</h3>
    <ul>
        <li><strong>Total Resources Analyzed:</strong> {report_data.get('resources_collected', 0)}</li>
        <li><strong>Potential Monthly Savings:</strong> ${total_savings:,.2f}</li>
        <li><strong>High Priority Actions:</strong> {high_priority}</li>
    </ul>
    
    <p><strong>Report Location:</strong> <code>{report_location}</code></p>
    
    <hr>
    <p><small>Generated at: {report_data.get('generated_at', 'Unknown')}</small></p>
    <p><small>Model Used: {report_data.get('model_used', 'Unknown')}</small></p>
</body>
</html>
"""
            
            # Send email
            response = ses_client.send_email(
                Source=self.config.email_from,
                Destination={'ToAddresses': self.config.email_to.split(',')},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Text': {'Data': body_text},
                        'Html': {'Data': body_html}
                    }
                }
            )
            
            self.logger.info(f"Notification sent successfully: {response['MessageId']}")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
            # Don't fail the entire process if notification fails


# Global controller instance (Singleton pattern)
controller = LambdaController()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function.
    
    This is the entry point for AWS Lambda execution.
    Routes requests to appropriate handlers based on event type.
    """
    try:
        # Determine request type
        request_type = event.get('request_type', 'analysis')
        
        if request_type == 'analysis':
            # Run async analysis
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(controller.handle_analysis_request(event))
                return result
            finally:
                loop.close()
                
        elif request_type == 'get_report':
            # Get specific report
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(controller.handle_report_request(event))
                return result
            finally:
                loop.close()
                
        elif request_type == 'list_reports':
            # List reports
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(controller.handle_list_reports_request(event))
                return result
            finally:
                loop.close()
                
        else:
            return {
                "statusCode": 400,
                "body": {"error": f"Unknown request type: {request_type}"}
            }
            
    except Exception as e:
        logging.error(f"Unhandled error in lambda_handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": {"error": "Internal server error"}
        }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "request_type": "analysis",
        "regions": ["us-east-1"],
        "analysis_period_days": 30,
        "include_cost_data": True,
        "save_report": True
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2, default=str))