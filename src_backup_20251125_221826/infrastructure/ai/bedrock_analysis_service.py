"""
Amazon Bedrock implementation of analysis service.
Uses Claude 3 for intelligent cost optimization analysis.
"""

import json
import boto3
import logging
from datetime import datetime
from typing import List, Dict, Any
from decimal import Decimal

from ...domain.entities import (
    AWSResource, 
    OptimizationRecommendation, 
    AnalysisReport,
    CostData,
    ResourceType,
    UsagePattern,
    Priority,
    RiskLevel
)
from ...domain.services.analysis_service import IAnalysisService, ResourceAnalyzer, ReportGenerator


class BedrockAnalysisService(IAnalysisService):
    """
    Amazon Bedrock implementation of analysis service.
    
    Uses Claude 3 for intelligent analysis following the Strategy Pattern.
    Implements the Template Method Pattern for analysis workflow.
    """

    def __init__(
        self, 
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: str = "us-east-1"
    ):
        self.model_id = model_id
        self.region = region
        self.logger = logging.getLogger(__name__)
        
        # Initialize Bedrock client (Singleton pattern)
        self._bedrock_client = None
        
        # Initialize domain services
        self.resource_analyzer = ResourceAnalyzer()
        self.report_generator = ReportGenerator()

    @property
    def bedrock_client(self):
        """Lazy initialization of Bedrock client."""
        if self._bedrock_client is None:
            self._bedrock_client = boto3.client('bedrock-runtime', region_name=self.region)
        return self._bedrock_client

    async def analyze_resource(self, resource: AWSResource) -> OptimizationRecommendation:
        """
        Analyze a single resource using Bedrock.
        
        Time Complexity: O(1) - single API call to Bedrock
        Space Complexity: O(1) - constant memory usage
        """
        try:
            # Prepare resource data for analysis
            resource_data = self._prepare_resource_data(resource)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(resource_data)
            
            # Call Bedrock for analysis
            bedrock_response = await self._call_bedrock(prompt)
            
            # Parse and validate response
            recommendation_data = self._parse_bedrock_response(bedrock_response)
            
            # Create recommendation object
            recommendation = self._create_recommendation(resource, recommendation_data)
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Failed to analyze resource {resource.resource_id}: {str(e)}")
            # Return a default "no recommendation" response
            return self._create_default_recommendation(resource)

    async def analyze_resources(self, resources: List[AWSResource]) -> List[OptimizationRecommendation]:
        """
        Analyze multiple resources in batch.
        
        Time Complexity: O(n/b) where n is resources and b is batch size
        Space Complexity: O(n)
        """
        recommendations = []
        batch_size = 10  # Process resources in batches to avoid token limits
        
        for i in range(0, len(resources), batch_size):
            batch = resources[i:i + batch_size]
            
            try:
                # Prepare batch data
                batch_data = [self._prepare_resource_data(resource) for resource in batch]
                
                # Create batch analysis prompt
                prompt = self._create_batch_analysis_prompt(batch_data)
                
                # Call Bedrock for batch analysis
                bedrock_response = await self._call_bedrock(prompt)
                
                # Parse batch response
                batch_recommendations = self._parse_batch_bedrock_response(bedrock_response, batch)
                
                recommendations.extend(batch_recommendations)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze batch starting at index {i}: {str(e)}")
                # Create default recommendations for failed batch
                for resource in batch:
                    recommendations.append(self._create_default_recommendation(resource))
        
        return recommendations

    async def generate_report(
        self, 
        resources: List[AWSResource], 
        cost_data: CostData,
        recommendations: List[OptimizationRecommendation]
    ) -> AnalysisReport:
        """
        Generate a complete analysis report.
        
        Time Complexity: O(r) where r is number of recommendations
        Space Complexity: O(r)
        """
        # Calculate aggregated savings
        savings = self.report_generator.aggregate_savings(recommendations)
        
        # Create analysis report
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version=self.report_generator.version,
            model_used=self.model_id,
            analysis_period_days=cost_data.period_days if cost_data else 30,
            total_resources_analyzed=len(resources),
            total_monthly_savings_usd=savings["monthly"],
            total_annual_savings_usd=savings["annual"],
            recommendations=recommendations,
            cost_data=cost_data
        )
        
        return report

    def _prepare_resource_data(self, resource: AWSResource) -> Dict[str, Any]:
        """
        Prepare resource data for Bedrock analysis.
        
        Time Complexity: O(m) where m is number of metrics
        Space Complexity: O(m)
        """
        # Calculate usage statistics
        cpu_stats = resource.metrics.get_cpu_stats()
        usage_pattern = self.resource_analyzer.calculate_usage_pattern(resource)
        
        return {
            "resource_id": resource.resource_id,
            "resource_type": resource.resource_type.value,
            "region": resource.region,
            "tags": resource.tags,
            "configuration": resource.configuration,
            "usage_pattern": usage_pattern.value,
            "cpu_statistics": cpu_stats,
            "is_production": resource.is_production(),
            "criticality": resource.get_criticality(),
            "metrics_data_points": len(resource.metrics.cpu_utilization),
            "created_at": resource.created_at.isoformat() if resource.created_at else None
        }

    def _create_analysis_prompt(self, resource_data: Dict[str, Any]) -> str:
        """
        Create analysis prompt for Bedrock.
        
        This prompt follows best practices for Claude 3:
        - Clear instructions
        - Structured output format
        - Domain expertise context
        """
        return f"""
You are an expert AWS FinOps analyst with deep knowledge of cloud cost optimization. 
Analyze the following AWS resource and provide optimization recommendations.

RESOURCE DATA:
{json.dumps(resource_data, indent=2)}

ANALYSIS REQUIREMENTS:
1. Analyze the resource's usage patterns and efficiency
2. Identify potential cost optimization opportunities
3. Consider production criticality and risk factors
4. Calculate potential savings with high accuracy
5. Provide specific implementation steps

OUTPUT FORMAT (JSON):
{{
    "analysis": {{
        "pattern": "steady|variable|batch|idle|unknown",
        "cpu_mean": <float>,
        "cpu_p95": <float>,
        "waste_percentage": <float 0-100>,
        "efficiency_score": <float 0-100>
    }},
    "recommendation": {{
        "action": "downsize|upsize|terminate|optimize|no_action",
        "details": "<specific recommendation>",
        "reasoning": "<detailed explanation>",
        "current_config": "<current configuration>",
        "recommended_config": "<recommended configuration>"
    }},
    "savings": {{
        "monthly_usd": <float>,
        "annual_usd": <float>,
        "percentage": <float 0-100>
    }},
    "risk_level": "low|medium|high",
    "priority": "high|medium|low",
    "confidence_score": <float 0-1>,
    "implementation_steps": [
        "<step 1>",
        "<step 2>",
        "..."
    ]
}}

IMPORTANT GUIDELINES:
- Be conservative with savings estimates
- Consider production workload requirements
- Factor in performance and availability needs
- Provide actionable, specific recommendations
- Include risk assessment and mitigation
- Ensure JSON is valid and complete

Analyze the resource now:
"""

    def _create_batch_analysis_prompt(self, batch_data: List[Dict[str, Any]]) -> str:
        """Create batch analysis prompt for multiple resources."""
        return f"""
You are an expert AWS FinOps analyst. Analyze the following batch of AWS resources 
and provide optimization recommendations for each.

RESOURCES DATA:
{json.dumps(batch_data, indent=2)}

Provide analysis for each resource in the following JSON array format:
[
    {{
        "resource_id": "<resource_id>",
        "analysis": {{ ... }},
        "recommendation": {{ ... }},
        "savings": {{ ... }},
        "risk_level": "low|medium|high",
        "priority": "high|medium|low",
        "confidence_score": <float 0-1>,
        "implementation_steps": [ ... ]
    }},
    ...
]

Follow the same analysis guidelines as for single resources.
Ensure the JSON array is valid and contains one entry per resource.
"""

    async def _call_bedrock(self, prompt: str) -> str:
        """
        Call Amazon Bedrock with the analysis prompt.
        
        Time Complexity: O(1) - single API call
        Space Complexity: O(p) where p is prompt size
        """
        try:
            # Prepare request body for Claude 3
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.1,  # Low temperature for consistent analysis
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            return response_body['content'][0]['text']
            
        except Exception as e:
            self.logger.error(f"Bedrock API call failed: {str(e)}")
            raise

    def _parse_bedrock_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Bedrock response and validate structure.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        try:
            # Extract JSON from response (handle potential markdown formatting)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['analysis', 'recommendation', 'savings', 'risk_level', 'priority']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to parse Bedrock response: {str(e)}")
            raise

    def _parse_batch_bedrock_response(
        self, 
        response: str, 
        resources: List[AWSResource]
    ) -> List[OptimizationRecommendation]:
        """Parse batch Bedrock response."""
        try:
            # Extract JSON array from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[json_start:json_end]
            batch_data = json.loads(json_str)
            
            recommendations = []
            
            # Create recommendations for each resource
            for i, resource in enumerate(resources):
                if i < len(batch_data):
                    rec_data = batch_data[i]
                    recommendation = self._create_recommendation(resource, rec_data)
                else:
                    # Fallback if response is incomplete
                    recommendation = self._create_default_recommendation(resource)
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to parse batch Bedrock response: {str(e)}")
            # Return default recommendations for all resources
            return [self._create_default_recommendation(resource) for resource in resources]

    def _create_recommendation(
        self, 
        resource: AWSResource, 
        recommendation_data: Dict[str, Any]
    ) -> OptimizationRecommendation:
        """
        Create OptimizationRecommendation from Bedrock response data.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        try:
            # Extract data with defaults
            analysis = recommendation_data.get('analysis', {})
            recommendation = recommendation_data.get('recommendation', {})
            savings = recommendation_data.get('savings', {})
            
            # Map string values to enums
            usage_pattern = self._map_usage_pattern(analysis.get('pattern', 'unknown'))
            risk_level = self._map_risk_level(recommendation_data.get('risk_level', 'medium'))
            priority = self._map_priority(recommendation_data.get('priority', 'medium'))
            
            return OptimizationRecommendation(
                resource_id=resource.resource_id,
                resource_type=resource.resource_type,
                current_config=recommendation.get('current_config', 'Unknown'),
                recommended_action=recommendation.get('action', 'no_action'),
                recommendation_details=recommendation.get('details', 'No recommendation available'),
                reasoning=recommendation.get('reasoning', 'Analysis incomplete'),
                monthly_savings_usd=Decimal(str(savings.get('monthly_usd', 0))),
                annual_savings_usd=Decimal(str(savings.get('annual_usd', 0))),
                savings_percentage=float(savings.get('percentage', 0)),
                risk_level=risk_level,
                priority=priority,
                implementation_steps=recommendation_data.get('implementation_steps', []),
                usage_pattern=usage_pattern,
                confidence_score=float(recommendation_data.get('confidence_score', 0.5))
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create recommendation for {resource.resource_id}: {str(e)}")
            return self._create_default_recommendation(resource)

    def _create_default_recommendation(self, resource: AWSResource) -> OptimizationRecommendation:
        """Create a default recommendation when analysis fails."""
        return OptimizationRecommendation(
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
            current_config="Unknown",
            recommended_action="review_manually",
            recommendation_details="Manual review required - automated analysis failed",
            reasoning="Insufficient data or analysis error",
            monthly_savings_usd=Decimal('0'),
            annual_savings_usd=Decimal('0'),
            savings_percentage=0.0,
            risk_level=RiskLevel.MEDIUM,
            priority=Priority.LOW,
            implementation_steps=["Review resource manually", "Analyze usage patterns", "Consider optimization opportunities"],
            usage_pattern=UsagePattern.UNKNOWN,
            confidence_score=0.0
        )

    def _map_usage_pattern(self, pattern_str: str) -> UsagePattern:
        """Map string to UsagePattern enum."""
        mapping = {
            'steady': UsagePattern.STEADY,
            'variable': UsagePattern.VARIABLE,
            'batch': UsagePattern.BATCH,
            'idle': UsagePattern.IDLE,
            'unknown': UsagePattern.UNKNOWN
        }
        return mapping.get(pattern_str.lower(), UsagePattern.UNKNOWN)

    def _map_risk_level(self, risk_str: str) -> RiskLevel:
        """Map string to RiskLevel enum."""
        mapping = {
            'low': RiskLevel.LOW,
            'medium': RiskLevel.MEDIUM,
            'high': RiskLevel.HIGH
        }
        return mapping.get(risk_str.lower(), RiskLevel.MEDIUM)

    def _map_priority(self, priority_str: str) -> Priority:
        """Map string to Priority enum."""
        mapping = {
            'high': Priority.HIGH,
            'medium': Priority.MEDIUM,
            'low': Priority.LOW
        }
        return mapping.get(priority_str.lower(), Priority.MEDIUM)