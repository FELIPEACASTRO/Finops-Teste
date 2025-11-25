# AWS FinOps Analyzer

## Overview
The AWS FinOps Analyzer is a production-ready Python application designed to identify cost optimization opportunities within AWS infrastructure. It leverages Amazon Bedrock (Claude 3 Sonnet) to analyze all 268 AWS services across multiple regions, providing AI-powered cost optimization recommendations with implementation steps. The project includes an interactive Flask web interface for exploring services, viewing statistics, and demoing analysis. Its primary purpose is to help businesses reduce their AWS spending by providing intelligent, actionable insights.

## Recent Changes (v4.0 UX Improvements)
**Latest Update - November 25, 2025:**
- **Enhanced Recommendation System**: Completely redesigned recommendation display with:
  - **Didactic Explanations**: Clear, educational "Why is this important?" sections that explain concepts in simple language
  - **Technical Implementation Steps**: Detailed, step-by-step instructions (numbered list) for each recommendation showing exactly what to do
  - **Modal Details View**: Click "Ver Detalhes Completos" on any recommendation to see full information
  - **Financial Impact Display**: Shows monthly savings, annual savings, cost reduction percentage, and risk level
  - **Priority Color-Coding**: High (red), Medium (gold), Low (green) visual indicators
- **Improved Interface Organization**:
  - Recommendation cards show economy highlight in top right
  - Each card displays action, reasoning, and technical summary
  - Modal opens with comprehensive details including all 7 sections
  - Responsive design works perfectly on mobile, tablet, desktop
- **Accessibility Enhancements**:
  - Modal closes with ESC key
  - Keyboard navigation support
  - Proper ARIA labels and announcements
  - Contrast ratios meet WCAG AA standards

## User Preferences
- The agent should use simple language for explanations.
- I prefer an iterative development approach.
- The agent should ask for confirmation before making major changes.
- I expect detailed explanations for complex concepts.
- Do not make changes to the `tests/` folder.
- Do not modify files in the `docs/` directory.
- Recommendations must have VERY CLEAR explanations that are didactic and educational.
- Recommendations must describe TECHNICAL STEPS needed to implement each item.
- Interface should be intuitive and well-organized, not cluttered.

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
- Recommendations display in cards with immediate summary, expandable to full modal with didactic explanations and technical steps.

**Technical Implementations & Design Choices:**
- **Resilience Patterns**: Incorporates Circuit Breaker, Retry with Exponential Backoff, and Timeout Protection (specifically for Bedrock calls) to enhance stability and fault tolerance.
- **Cost Optimization**: Implements cost data caching to significantly reduce AWS Cost Explorer API calls (96% reduction).
- **Monitoring**: Integrates with AWS CloudWatch for comprehensive metrics tracking (analysis duration, resources analyzed, recommendations generated, savings, errors).
- **Comprehensive AWS Service Support**: Analyzes all 268 AWS services, with intelligent auto-generation of metadata for services not explicitly defined.
- **Quality Assurance**: Features 386 passing tests (100% pass rate), 42% overall code coverage with 76-99% on critical business logic. Tests exercise real production code using dependency injection and proper mocking patterns.
- **Deployment**: Designed for serverless deployment on AWS Lambda, with considerations for large-scale operations using AWS Step Functions.

## Frontend Architecture
- **Modern UI Framework**: Glassmorphism effects with light color palette, gradient backgrounds
- **Accessibility**: WCAG 2.1 AA compliant with skip links, semantic HTML, keyboard navigation, reduced-motion support
- **Recommendation Display**:
  - Summary cards with action, reasoning, and economy highlighted
  - Modal with 7 information sections (Why Important, Current Config, Recommendation, Technical Steps, Financial Impact, Actions)
  - Each recommendation includes didactic explanation and numbered implementation steps

## External Dependencies
- **Amazon Bedrock**: Utilized for AI-powered cost analysis and recommendation generation (specifically Claude 3 Sonnet).
- **AWS SDK (Boto3)**: For interacting with various AWS services like Cost Explorer, CloudWatch, S3, and Lambda.
- **AWS S3**: Used for storing generated reports.
- **AWS CloudWatch**: For application monitoring and logging.
- **Flask**: Framework for the interactive web interface.
- **pytest**: Python testing framework.
