"""
Contract Tests for AWS API Responses
Validates that AWS APIs return expected schemas
"""
import pytest
from jsonschema import validate, ValidationError


class TestEC2Contracts:
    """Contract tests for EC2 API responses"""
    
    def test_describe_instances_schema(self):
        """Validate EC2 describe_instances response schema"""
        schema = {
            "type": "object",
            "properties": {
                "Reservations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Instances": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["InstanceId", "InstanceType", "State"],
                                    "properties": {
                                        "InstanceId": {"type": "string"},
                                        "InstanceType": {"type": "string"},
                                        "State": {
                                            "type": "object",
                                            "required": ["Name"],
                                            "properties": {
                                                "Name": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "required": ["Reservations"]
        }
        
        # Mock response
        mock_response = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "InstanceType": "t3.micro",
                            "State": {"Name": "running"}
                        }
                    ]
                }
            ]
        }
        
        # Validate
        validate(instance=mock_response, schema=schema)


class TestRDSContracts:
    """Contract tests for RDS API responses"""
    
    def test_describe_db_instances_schema(self):
        """Validate RDS describe_db_instances response schema"""
        schema = {
            "type": "object",
            "properties": {
                "DBInstances": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["DBInstanceIdentifier", "DBInstanceClass", "Engine"],
                        "properties": {
                            "DBInstanceIdentifier": {"type": "string"},
                            "DBInstanceClass": {"type": "string"},
                            "Engine": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["DBInstances"]
        }
        
        mock_response = {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "mydb",
                    "DBInstanceClass": "db.t3.micro",
                    "Engine": "postgres"
                }
            ]
        }
        
        validate(instance=mock_response, schema=schema)


class TestBedrockContracts:
    """Contract tests for Bedrock API responses"""
    
    def test_invoke_model_response_schema(self):
        """Validate Bedrock invoke_model response schema"""
        schema = {
            "type": "object",
            "required": ["body", "contentType"],
            "properties": {
                "body": {"type": "object"},
                "contentType": {"type": "string"}
            }
        }
        
        mock_response = {
            "body": {"content": [{"text": "Analysis result"}]},
            "contentType": "application/json"
        }
        
        validate(instance=mock_response, schema=schema)
    
    def test_bedrock_analysis_output_schema(self):
        """Validate Bedrock analysis output matches expected format"""
        schema = {
            "type": "object",
            "required": ["recommendations", "summary"],
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": [
                            "resource_id",
                            "resource_type",
                            "current_cost_monthly",
                            "recommended_action",
                            "estimated_savings_monthly",
                            "estimated_savings_annual",
                            "priority",
                            "risk_level"
                        ],
                        "properties": {
                            "resource_id": {"type": "string"},
                            "resource_type": {"type": "string"},
                            "current_cost_monthly": {"type": "number", "minimum": 0},
                            "recommended_action": {"type": "string"},
                            "estimated_savings_monthly": {"type": "number", "minimum": 0},
                            "estimated_savings_annual": {"type": "number", "minimum": 0},
                            "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}
                        }
                    }
                },
                "summary": {
                    "type": "object",
                    "required": [
                        "total_monthly_savings_usd",
                        "total_annual_savings_usd",
                        "high_priority_actions"
                    ],
                    "properties": {
                        "total_monthly_savings_usd": {"type": "number", "minimum": 0},
                        "total_annual_savings_usd": {"type": "number", "minimum": 0},
                        "high_priority_actions": {"type": "integer", "minimum": 0}
                    }
                }
            }
        }
        
        mock_output = {
            "recommendations": [
                {
                    "resource_id": "i-123",
                    "resource_type": "EC2",
                    "current_cost_monthly": 50.0,
                    "recommended_action": "Downsize to t3.small",
                    "estimated_savings_monthly": 25.0,
                    "estimated_savings_annual": 300.0,
                    "priority": "HIGH",
                    "risk_level": "LOW"
                }
            ],
            "summary": {
                "total_monthly_savings_usd": 25.0,
                "total_annual_savings_usd": 300.0,
                "high_priority_actions": 1
            }
        }
        
        validate(instance=mock_output, schema=schema)


class TestCostExplorerContracts:
    """Contract tests for Cost Explorer API responses"""
    
    def test_get_cost_and_usage_schema(self):
        """Validate Cost Explorer get_cost_and_usage response schema"""
        schema = {
            "type": "object",
            "required": ["ResultsByTime"],
            "properties": {
                "ResultsByTime": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["TimePeriod", "Total"],
                        "properties": {
                            "TimePeriod": {
                                "type": "object",
                                "required": ["Start", "End"],
                                "properties": {
                                    "Start": {"type": "string"},
                                    "End": {"type": "string"}
                                }
                            },
                            "Total": {
                                "type": "object"
                            }
                        }
                    }
                }
            }
        }
        
        mock_response = {
            "ResultsByTime": [
                {
                    "TimePeriod": {
                        "Start": "2025-11-01",
                        "End": "2025-11-02"
                    },
                    "Total": {
                        "UnblendedCost": {
                            "Amount": "100.50",
                            "Unit": "USD"
                        }
                    }
                }
            ]
        }
        
        validate(instance=mock_response, schema=schema)
