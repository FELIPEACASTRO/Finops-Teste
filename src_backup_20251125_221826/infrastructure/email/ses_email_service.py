"""
Amazon SES Email Service Implementation
Sends FinOps analysis reports via email
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SESEmailService:
    """Service for sending emails via Amazon SES"""
    
    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize SES Email Service
        
        Args:
            region: AWS region for SES
        """
        self.ses_client = boto3.client('ses', region_name=region)
        self.region = region
        
    def send_report_email(
        self,
        sender: str,
        recipients: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[dict]] = None
    ) -> dict:
        """
        Send FinOps report email
        
        Args:
            sender: Email address of sender (must be verified in SES)
            recipients: List of recipient email addresses
            subject: Email subject
            html_body: HTML body content
            text_body: Plain text body content (optional)
            attachments: List of attachments (not implemented yet)
            
        Returns:
            dict: Response from SES with MessageId
            
        Raises:
            ClientError: If email sending fails
        """
        try:
            # Build email message
            message = {
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
            
            # Add text body if provided
            if text_body:
                message['Body']['Text'] = {
                    'Data': text_body,
                    'Charset': 'UTF-8'
                }
            
            # Send email
            response = self.ses_client.send_email(
                Source=sender,
                Destination={
                    'ToAddresses': recipients
                },
                Message=message
            )
            
            logger.info(f"Email sent successfully. MessageId: {response['MessageId']}")
            return response
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to send email. Error: {error_code} - {error_message}")
            raise
            
    def send_finops_analysis_report(
        self,
        sender: str,
        recipients: List[str],
        report_data: dict,
        report_html: str,
        s3_report_url: Optional[str] = None
    ) -> dict:
        """
        Send FinOps analysis report with formatted content
        
        Args:
            sender: Sender email address
            recipients: List of recipient emails
            report_data: Dictionary with report summary data
            report_html: Full HTML report content
            s3_report_url: Optional S3 URL for full report
            
        Returns:
            dict: SES response
        """
        # Extract summary data
        total_savings_monthly = report_data.get('summary', {}).get('total_monthly_savings_usd', 0)
        total_savings_annual = report_data.get('summary', {}).get('total_annual_savings_usd', 0)
        high_priority = report_data.get('summary', {}).get('high_priority_actions', 0)
        resources_analyzed = report_data.get('resources_analyzed', 0)
        
        # Build subject
        subject = f"FinOps Analysis Report - ${total_savings_monthly:,.2f}/month savings identified"
        
        # Build email body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px 20px; text-align: center; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #28a745; }}
        .metric-label {{ font-size: 14px; color: #666; }}
        .cta {{ background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 FinOps Analysis Report</h1>
            <p>Automated Cost Optimization Analysis</p>
            <p>{datetime.now().strftime('%B %d, %Y')}</p>
        </div>
        
        <div class="summary">
            <h2>💰 Savings Opportunity</h2>
            <div class="metric">
                <div class="metric-value">${total_savings_monthly:,.2f}</div>
                <div class="metric-label">Monthly Savings</div>
            </div>
            <div class="metric">
                <div class="metric-value">${total_savings_annual:,.2f}</div>
                <div class="metric-label">Annual Savings</div>
            </div>
            <div class="metric">
                <div class="metric-value">{high_priority}</div>
                <div class="metric-label">High Priority Actions</div>
            </div>
            <div class="metric">
                <div class="metric-value">{resources_analyzed}</div>
                <div class="metric-label">Resources Analyzed</div>
            </div>
        </div>
        
        <h2>📊 Key Highlights</h2>
        <ul>
            <li><strong>Total Potential Savings:</strong> ${total_savings_annual:,.2f} per year</li>
            <li><strong>High Priority Actions:</strong> {high_priority} recommendations require immediate attention</li>
            <li><strong>Resources Analyzed:</strong> {resources_analyzed} AWS resources across multiple services</li>
            <li><strong>Analysis Period:</strong> Last 30 days</li>
        </ul>
        
        {f'<p><a href="{s3_report_url}" class="cta">📥 Download Full Report</a></p>' if s3_report_url else ''}
        
        <div class="footer">
            <p>This is an automated report generated by AWS FinOps Analyzer v4.0</p>
            <p>Powered by Amazon Bedrock (Claude 3 Sonnet)</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Plain text version
        text_body = f"""
FinOps Analysis Report - {datetime.now().strftime('%B %d, %Y')}

SAVINGS OPPORTUNITY:
- Monthly Savings: ${total_savings_monthly:,.2f}
- Annual Savings: ${total_savings_annual:,.2f}
- High Priority Actions: {high_priority}
- Resources Analyzed: {resources_analyzed}

KEY HIGHLIGHTS:
- Total Potential Savings: ${total_savings_annual:,.2f} per year
- High Priority Actions: {high_priority} recommendations require immediate attention
- Resources Analyzed: {resources_analyzed} AWS resources
- Analysis Period: Last 30 days

{f'Full Report: {s3_report_url}' if s3_report_url else ''}

---
This is an automated report generated by AWS FinOps Analyzer v4.0
Powered by Amazon Bedrock (Claude 3 Sonnet)
"""
        
        return self.send_report_email(
            sender=sender,
            recipients=recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        
    def verify_email_address(self, email: str) -> dict:
        """
        Verify an email address in SES
        
        Args:
            email: Email address to verify
            
        Returns:
            dict: SES response
        """
        try:
            response = self.ses_client.verify_email_identity(
                EmailAddress=email
            )
            logger.info(f"Verification email sent to {email}")
            return response
        except ClientError as e:
            logger.error(f"Failed to verify email {email}: {e}")
            raise
            
    def get_send_quota(self) -> dict:
        """
        Get SES sending quota
        
        Returns:
            dict: Quota information (Max24HourSend, MaxSendRate, SentLast24Hours)
        """
        try:
            response = self.ses_client.get_send_quota()
            return response
        except ClientError as e:
            logger.error(f"Failed to get send quota: {e}")
            raise
