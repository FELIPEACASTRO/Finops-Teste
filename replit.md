# AWS FinOps Analyzer

## Overview
The AWS FinOps Analyzer is a production-ready Python application designed to identify cost optimization opportunities within AWS infrastructure. It leverages Amazon Bedrock (Claude 3 Sonnet) to analyze all 268 AWS services across multiple regions, providing AI-powered cost optimization recommendations with implementation steps. The project includes an interactive Flask web interface for exploring services, viewing statistics, and demoing analysis. Its primary purpose is to help businesses reduce their AWS spending by providing intelligent, actionable insights.

## User Preferences
- The agent should use simple language for explanations.
- I prefer an iterative development approach.
- The agent should ask for confirmation before making major changes.
- I expect detailed explanations for complex concepts.
- Do not make changes to the `tests/` folder.
- Do not modify files in the `docs/` directory.

## System Architecture
The application adheres to a Clean Architecture with Domain-Driven Design principles, promoting testability, maintainability, and flexibility.

**Core Architectural Layers:**
- **Interfaces**: Handles external interactions (e.g., AWS Lambda, CLI, Web Interface).
- **Application Layer**: Contains use cases and Data Transfer Objects (DTOs).
- **Domain Layer**: Encapsulates core business logic, entities, and services.
- **Infrastructure Layer**: Manages external concerns like resilience (Circuit Breaker, Retry with Exponential Backoff), caching (Cost Data TTL), monitoring (CloudWatch Metrics), AWS SDK interactions, and AI integration (Amazon Bedrock with timeout protection).

**UI/UX Decisions (Web Interface):**
- An interactive Flask web application provides a user-friendly interface to explore AWS services, view project statistics, and see demo cost analyses.
- Services are categorized into 24 distinct groups (e.g., Compute, Storage, Database, AI/ML, IoT, Quantum).

**Technical Implementations & Design Choices:**
- **Resilience Patterns**: Incorporates Circuit Breaker, Retry with Exponential Backoff, and Timeout Protection (specifically for Bedrock calls) to enhance stability and fault tolerance.
- **Cost Optimization**: Implements cost data caching to significantly reduce AWS Cost Explorer API calls (96% reduction).
- **Monitoring**: Integrates with AWS CloudWatch for comprehensive metrics tracking (analysis duration, resources analyzed, recommendations generated, savings, errors).
- **Comprehensive AWS Service Support**: Analyzes all 268 AWS services, with intelligent auto-generation of metadata for services not explicitly defined.
- **Quality Assurance**: Features 386 passing tests (100% pass rate), 42% overall code coverage with 76-99% on critical business logic. Tests exercise real production code using dependency injection and proper mocking patterns.
- **Deployment**: Designed for serverless deployment on AWS Lambda, with considerations for large-scale operations using AWS Step Functions.

## External Dependencies
- **Amazon Bedrock**: Utilized for AI-powered cost analysis and recommendation generation (specifically Claude 3 Sonnet).
- **AWS SDK (Boto3)**: For interacting with various AWS services like Cost Explorer, CloudWatch, S3, and Lambda.
- **AWS S3**: Used for storing generated reports.
- **AWS CloudWatch**: For application monitoring and logging.
- **Flask**: Framework for the interactive web interface.
- **pytest**: Python testing framework.