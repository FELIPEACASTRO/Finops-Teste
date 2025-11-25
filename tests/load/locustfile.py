"""
Load Tests for AWS FinOps Analyzer
Tests system behavior under high load
"""
from locust import HttpUser, task, between
import json


class FinOpsAnalyzerUser(HttpUser):
    """Simulated user for load testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    @task(3)
    def analyze_resources(self):
        """Test resource analysis endpoint"""
        payload = {
            "regions": ["us-east-1"],
            "period_days": 7,
            "resource_types": ["EC2", "RDS"]
        }
        
        with self.client.post(
            "/api/analyze",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def get_recommendations(self):
        """Test recommendations endpoint"""
        with self.client.get(
            "/api/recommendations",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "recommendations" in data:
                    response.success()
                else:
                    response.failure("Missing recommendations in response")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def get_summary(self):
        """Test summary endpoint"""
        with self.client.get(
            "/api/summary",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    def on_start(self):
        """Called when a simulated user starts"""
        pass


class StressTestUser(HttpUser):
    """Stress test with large payloads"""
    
    wait_time = between(2, 5)
    
    @task
    def analyze_large_dataset(self):
        """Test with large number of resources"""
        payload = {
            "regions": ["us-east-1", "us-west-2", "eu-west-1"],
            "period_days": 30,
            "resource_types": ["EC2", "RDS", "ELB", "Lambda", "EBS", "S3", "DynamoDB", "ElastiCache"]
        }
        
        with self.client.post(
            "/api/analyze",
            json=payload,
            timeout=300,  # 5 minutes
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 504:
                response.failure("Timeout - Lambda execution exceeded limit")
            else:
                response.failure(f"Got status code {response.status_code}")
