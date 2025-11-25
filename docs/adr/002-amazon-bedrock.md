# ADR 002: Amazon Bedrock for AI Analysis

**Date**: 2025-11-25

**Status**: Accepted

## Context

The FinOps Analyzer needs to perform intelligent analysis of AWS resource usage to generate cost-saving recommendations. This requires advanced reasoning and contextual understanding.

## Decision

We will use **Amazon Bedrock** with the **Claude 3 Sonnet** model for all AI-driven analysis. The application will collect raw data and send it to Bedrock via a detailed prompt, receiving structured JSON output.

## Consequences

**Pros**:
- **Powerful AI**: Leverages state-of-the-art generative AI for deep analysis.
- **Simplified Code**: No need to develop and maintain complex ML models.
- **Flexibility**: Easy to update the prompt to change analysis logic.
- **Cost-Effective**: Pay-per-use model is cheaper than training custom models.

**Cons**:
- **External Dependency**: Reliant on the availability and performance of Bedrock.
- **Prompt Engineering**: Requires careful crafting and maintenance of the prompt.
- **Potential for Latency**: API calls to Bedrock can add latency.
