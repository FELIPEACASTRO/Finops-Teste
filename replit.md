# AWS FinOps Analyzer v4.0

## Overview

This is an **AWS FinOps (Financial Operations) Analyzer** - a Python-based application that uses Amazon Bedrock (Claude 3) to analyze AWS resources and provide intelligent cost optimization recommendations.

### Purpose

The application analyzes AWS infrastructure (EC2, RDS, ELB, Lambda, EBS) to identify cost optimization opportunities and provides actionable recommendations backed by AI analysis.

### Key Features

- Analyzes EC2, RDS, ELB, Lambda, and EBS resources
- Uses Amazon Bedrock (Claude 3 Sonnet) for AI-powered analysis
- Provides detailed cost savings recommendations with implementation steps
- Generates comprehensive JSON reports
- Supports multiple AWS regions
- Can send email notifications via AWS SES

## Architecture

This project follows **Clean Architecture** principles with **Domain-Driven Design**:

```
src/
├── application/          # Use cases and DTOs
├── core/                # Configuration and utilities
├── domain/              # Business entities and services
├── infrastructure/      # AWS integrations (Bedrock, CloudWatch, etc.)
└── interfaces/          # Entry points (Lambda handler, CLI)
```

### Primary Use Case

- **AWS Lambda Function**: Deployed to AWS Lambda, scheduled to run daily via EventBridge
- **CLI Tool**: For local testing and manual execution

## Current State (Replit Environment)

Since this is a Replit environment without AWS credentials, the project is configured to run a **demo mode** that:

1. Shows the application's capabilities and structure
2. Displays sample analysis output
3. Provides CLI usage examples
4. Demonstrates the configuration options

The demo runs automatically when you start the Replit.

## Project Structure

- `src/` - Main application code following Clean Architecture
- `tests/` - Unit and integration tests
- `demo.py` - Demo script for Replit environment
- `requirements.txt` - Python dependencies
- `cloudformation-*.yaml` - CloudFormation templates for AWS deployment
- `lambda_finops_*.py` - Legacy Lambda implementations (v3)

## Environment Variables

The following environment variables are configured for demo purposes:

| Variable | Value | Description |
|----------|-------|-------------|
| `AWS_REGION` | us-east-1 | AWS region for analysis |
| `S3_BUCKET_NAME` | finops-reports-demo | S3 bucket for reports |
| `BEDROCK_MODEL_ID` | anthropic.claude-3-sonnet-20240229-v1:0 | Bedrock model |
| `HISTORICAL_DAYS` | 30 | Days of metrics to analyze |
| `LOG_LEVEL` | INFO | Logging level |
| `ENVIRONMENT` | development | Environment type |

## Running the Application

### In Replit (Demo Mode)

The demo runs automatically via the "Demo" workflow. You can also run it manually:

```bash
python demo.py
```

### With AWS Credentials (Not in Replit)

If you have AWS credentials configured:

```bash
# Run analysis
python -m src.main analyze --regions us-east-1 --days 30

# Get a saved report
python -m src.main get-report --report-id <report-id>

# List recent reports
python -m src.main list-reports --limit 5
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_domain_entities.py
```

## AWS Deployment

To deploy this to AWS Lambda:

1. **Prerequisites**:
   - AWS account with appropriate permissions
   - Amazon Bedrock enabled in your region
   - Claude 3 Sonnet model access approved
   - S3 bucket created for reports

2. **Deploy via CloudFormation**:
   ```bash
   aws cloudformation deploy \
     --template-file cloudformation-v4.yaml \
     --stack-name finops-analyzer \
     --capabilities CAPABILITY_NAMED_IAM
   ```

3. **Schedule with EventBridge** for daily execution

See `DEPLOY_GUIDE.md` for detailed deployment instructions.

## Documentation

- `README.md` - Comprehensive project documentation
- `DEPLOY_GUIDE.md` - AWS deployment guide
- `BEDROCK_SETUP_GUIDE.md` - Bedrock configuration
- `TROUBLESHOOTING.md` - Common issues and solutions
- `FAQ.md` - Frequently asked questions

## Technology Stack

- **Language**: Python 3.11
- **Cloud Provider**: AWS
- **AI Service**: Amazon Bedrock (Claude 3 Sonnet)
- **AWS Services**: Lambda, CloudWatch, Cost Explorer, S3, SES
- **Testing**: pytest, pytest-asyncio
- **Code Quality**: black, flake8, mypy

## Cost Optimization Results

Typical savings identified:

- EC2 instances: 40-60% by rightsizing
- RDS databases: 50-70% by downsizing
- Unused EBS volumes: 100% by deletion
- Over-provisioned Lambda: 30-50% by memory adjustment

## Recent Changes

- **2024-11-24**: Project imported to Replit
  - Added demo.py for demonstration without AWS credentials
  - Configured environment variables for local testing
  - Set up workflow to run demo automatically

## Development Preferences

This project uses:

- Clean Architecture with Domain-Driven Design
- Type hints and mypy for type checking
- pytest for testing
- black for code formatting
- Async/await patterns for I/O operations

## License

MIT License - See LICENSE file for details
