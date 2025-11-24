#!/usr/bin/env python3
"""
Demo script for AWS FinOps Analyzer v4.0

This script demonstrates the application's capabilities without requiring AWS credentials.
It shows the CLI interface, configuration options, and example output structure.
"""

import json
import sys
from datetime import datetime


def print_header():
    """Print application header."""
    print("=" * 70)
    print("🤖 AWS FinOps Analyzer v4.0 - Demo Mode")
    print("=" * 70)
    print()


def print_section(title):
    """Print section title."""
    print(f"\n{'─' * 70}")
    print(f"📋 {title}")
    print('─' * 70)


def show_overview():
    """Show application overview."""
    print_section("Application Overview")
    
    overview = """
This is an AWS FinOps Analyzer that uses Amazon Bedrock (Claude 3) to analyze
AWS resources and provide intelligent cost optimization recommendations.

Key Features:
  ✅ Analyzes EC2, RDS, ELB, Lambda, and EBS resources
  ✅ Uses Amazon Bedrock (Claude 3 Sonnet) for AI-powered analysis
  ✅ Provides detailed cost savings recommendations
  ✅ Generates comprehensive reports saved to S3
  ✅ Supports multiple AWS regions
  ✅ Can send email notifications via SES

Architecture:
  - Clean Architecture with Domain-Driven Design
  - Primary: AWS Lambda function
  - Secondary: CLI tool for local testing
"""
    print(overview)


def show_cli_usage():
    """Show CLI usage examples."""
    print_section("CLI Usage Examples")
    
    examples = """
Run cost optimization analysis:
  $ python -m src.main analyze --regions us-east-1,us-west-2 --days 30

Get a saved report:
  $ python -m src.main get-report --report-id finops-analysis-20241124-120000

List recent reports:
  $ python -m src.main list-reports --limit 5

Help:
  $ python -m src.main --help
"""
    print(examples)


def show_configuration():
    """Show configuration options."""
    print_section("Configuration (Environment Variables)")
    
    config = [
        ("AWS_REGION", "us-east-1", "AWS region for analysis"),
        ("S3_BUCKET_NAME", "finops-reports", "S3 bucket for reports"),
        ("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0", "Bedrock model"),
        ("HISTORICAL_DAYS", "30", "Days of metrics to analyze"),
        ("EMAIL_FROM", "sender@example.com", "Email sender (optional)"),
        ("EMAIL_TO", "recipient@example.com", "Email recipients (optional)"),
        ("LOG_LEVEL", "INFO", "Logging level"),
    ]
    
    print(f"\n{'Variable':<30} {'Default':<45} {'Description':<30}")
    print('-' * 105)
    for var, default, desc in config:
        print(f"{var:<30} {default:<45} {desc:<30}")


def show_sample_analysis():
    """Show sample analysis output."""
    print_section("Sample Analysis Output")
    
    sample = {
        "generated_at": datetime.now().isoformat() + "Z",
        "version": "4.0-bedrock",
        "model_used": "anthropic.claude-3-sonnet-20240229-v1:0",
        "analysis_period_days": 30,
        "resources_analyzed": 45,
        "summary": {
            "total_monthly_savings_usd": 1234.56,
            "total_annual_savings_usd": 14814.72,
            "high_priority_actions": 8,
            "medium_priority_actions": 12,
            "low_priority_actions": 5
        },
        "sample_recommendation": {
            "resource_type": "EC2",
            "resource_id": "i-1234567890abcdef0",
            "current_config": "t3a.large (2 vCPU, 8GB RAM)",
            "recommendation": {
                "action": "downsize",
                "details": "Downsize from t3a.large to t3a.medium",
                "reasoning": "CPU usage avg 21.3%, p95 31.2% - 70% capacity unused"
            },
            "savings": {
                "monthly_usd": 27.37,
                "annual_usd": 328.44,
                "percentage": 50
            },
            "risk_level": "low",
            "priority": "high"
        }
    }
    
    print(json.dumps(sample, indent=2))


def show_deployment():
    """Show deployment information."""
    print_section("AWS Lambda Deployment")
    
    deployment = """
This application is designed to run as an AWS Lambda function:

1. Deploy using CloudFormation:
   $ aws cloudformation deploy \\
       --template-file cloudformation-v4.yaml \\
       --stack-name finops-analyzer \\
       --capabilities CAPABILITY_NAMED_IAM

2. Required IAM permissions:
   - ec2:DescribeInstances, ec2:DescribeVolumes
   - rds:DescribeDBInstances
   - elasticloadbalancing:DescribeLoadBalancers
   - lambda:ListFunctions
   - cloudwatch:GetMetricStatistics
   - ce:GetCostAndUsage
   - bedrock:InvokeModel
   - s3:PutObject
   - ses:SendEmail (optional)

3. Schedule with EventBridge:
   - Daily execution at 8 AM
   - Automatic report generation
   - Email notifications
"""
    print(deployment)


def show_required_setup():
    """Show what's required to run this in AWS."""
    print_section("AWS Requirements")
    
    requirements = """
To run this application with real AWS resources, you need:

1. ✓ AWS Account with appropriate permissions
2. ✓ Amazon Bedrock enabled in your region
3. ✓ Claude 3 Sonnet model access approved
4. ✓ S3 bucket created for reports
5. ✓ (Optional) SES configured for email notifications

Note: This demo runs without AWS credentials to show the structure
      and capabilities. To analyze real resources, deploy to AWS Lambda
      or configure AWS credentials locally.
"""
    print(requirements)


def show_project_structure():
    """Show project structure."""
    print_section("Project Structure")
    
    structure = """
src/
├── application/          # Application layer (use cases)
│   ├── dto/             # Data Transfer Objects
│   └── use_cases/       # Business logic orchestration
├── core/                # Core configuration and utilities
│   ├── config.py        # Centralized configuration
│   └── logger.py        # Logging setup
├── domain/              # Domain layer (business entities)
│   ├── entities/        # Resource entities
│   ├── repositories/    # Repository interfaces
│   └── services/        # Domain services
├── infrastructure/      # Infrastructure layer
│   ├── ai/             # Bedrock AI integration
│   ├── aws/            # AWS service clients
│   └── email/          # Email notifications
├── interfaces/          # Interface layer
│   └── lambda_handler.py  # Lambda entry point
└── main.py             # CLI entry point

tests/
├── unit/               # Unit tests
└── integration/        # Integration tests
"""
    print(structure)


def show_tests():
    """Show how to run tests."""
    print_section("Running Tests")
    
    test_info = """
Run all tests:
  $ pytest

Run with coverage:
  $ pytest --cov=src --cov-report=html

Run specific test file:
  $ pytest tests/unit/test_domain_entities.py

Run integration tests:
  $ pytest tests/integration/
"""
    print(test_info)


def main():
    """Main demo function."""
    print_header()
    
    # Show all sections
    show_overview()
    show_required_setup()
    show_cli_usage()
    show_configuration()
    show_project_structure()
    show_sample_analysis()
    show_deployment()
    show_tests()
    
    # Footer
    print("\n" + "=" * 70)
    print("📚 For more information, see:")
    print("   - README.md for detailed documentation")
    print("   - DEPLOY_GUIDE.md for deployment instructions")
    print("   - BEDROCK_SETUP_GUIDE.md for Bedrock configuration")
    print("=" * 70)
    print("\n✨ Demo completed successfully!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error running demo: {str(e)}")
        sys.exit(1)
