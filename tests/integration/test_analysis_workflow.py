"""
Integration tests for the complete analysis workflow.
Tests the interaction between different layers of the application.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from decimal import Decimal

from src.application.use_cases.analyze_resources_use_case import (
    AnalyzeResourcesUseCase,
    AnalyzeResourcesCommand
)
from src.domain.entities import (
    AWSResource,
    ResourceType,
    OptimizationRecommendation,
    Priority,
    RiskLevel,
    UsagePattern,
    CostData,
    AnalysisReport
)


class TestAnalysisWorkflow:
    """Integration tests for the complete analysis workflow."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories for testing."""
        resource_repo = Mock()
        cost_repo = Mock()
        report_repo = Mock()
        
        # Mock resource repository
        resource_repo.get_all_resources = AsyncMock(return_value=[
            AWSResource(
                resource_id="i-1234567890abcdef0",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                account_id="123456789012",
                tags={"Environment": "production", "Team": "backend"},
                configuration={"instance_type": "t3a.large", "state": "running"}
            ),
            AWSResource(
                resource_id="db-instance-1",
                resource_type=ResourceType.RDS,
                region="us-east-1",
                account_id="123456789012",
                tags={"Environment": "production", "Team": "backend"},
                configuration={"db_instance_class": "db.m5.large", "engine": "postgres"}
            )
        ])
        
        # Mock cost repository
        cost_repo.get_cost_data = AsyncMock(return_value=CostData(
            total_cost_usd=Decimal('1500.00'),
            period_days=30,
            cost_by_service={'EC2': Decimal('800.00'), 'RDS': Decimal('700.00')}
        ))
        
        # Mock report repository
        report_repo.save_report = AsyncMock(return_value="s3://bucket/report.json")
        
        return resource_repo, cost_repo, report_repo
    
    @pytest.fixture
    def mock_analysis_service(self):
        """Create mock analysis service for testing."""
        service = Mock()
        
        # Mock analyze_resources method
        service.analyze_resources = AsyncMock(return_value=[
            OptimizationRecommendation(
                resource_id="i-1234567890abcdef0",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Downsize to t3a.medium",
                reasoning="CPU utilization is consistently low at 20%",
                monthly_savings_usd=Decimal('50.00'),
                annual_savings_usd=Decimal('600.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH,
                usage_pattern=UsagePattern.STEADY,
                confidence_score=0.85,
                implementation_steps=["Create AMI", "Stop instance", "Change type", "Start instance"]
            ),
            OptimizationRecommendation(
                resource_id="db-instance-1",
                resource_type=ResourceType.RDS,
                current_config="db.m5.large",
                recommended_action="downsize",
                recommendation_details="Downsize to db.t3.medium",
                reasoning="Low connection count and CPU utilization",
                monthly_savings_usd=Decimal('100.00'),
                annual_savings_usd=Decimal('1200.00'),
                savings_percentage=40.0,
                risk_level=RiskLevel.MEDIUM,
                priority=Priority.MEDIUM,
                usage_pattern=UsagePattern.STEADY,
                confidence_score=0.75,
                implementation_steps=["Schedule maintenance window", "Modify instance class"]
            )
        ])
        
        # Mock generate_report method
        service.generate_report = AsyncMock(return_value=AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="anthropic.claude-3-sonnet-20240229-v1:0",
            analysis_period_days=30,
            total_resources_analyzed=2,
            total_monthly_savings_usd=Decimal('150.00'),
            total_annual_savings_usd=Decimal('1800.00'),
            recommendations=[],  # Will be populated by the use case
            cost_data=CostData(
                total_cost_usd=Decimal('1500.00'),
                period_days=30,
                cost_by_service={'EC2': Decimal('800.00'), 'RDS': Decimal('700.00')}
            )
        ))
        
        return service
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, mock_repositories, mock_analysis_service):
        """Test the complete analysis workflow from start to finish."""
        resource_repo, cost_repo, report_repo = mock_repositories
        
        # Create use case with mocked dependencies
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=mock_analysis_service
        )
        
        # Create command
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        # Execute use case
        result = await use_case.execute(command)
        
        # Verify success
        assert result.success is True
        assert result.report is not None
        assert result.report_location == "s3://bucket/report.json"
        assert result.message == "Analysis completed successfully"
        
        # Verify repository calls
        resource_repo.get_all_resources.assert_called_once_with(["us-east-1"])
        cost_repo.get_cost_data.assert_called_once()
        report_repo.save_report.assert_called_once()
        
        # Verify analysis service calls
        mock_analysis_service.analyze_resources.assert_called_once()
        mock_analysis_service.generate_report.assert_called_once()
        
        # Verify report content
        assert result.report.total_resources_analyzed == 2
        assert result.report.total_monthly_savings_usd == Decimal('150.00')
    
    @pytest.mark.asyncio
    async def test_analysis_workflow_without_cost_data(self, mock_repositories, mock_analysis_service):
        """Test analysis workflow without cost data collection."""
        resource_repo, cost_repo, report_repo = mock_repositories
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=mock_analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=False,  # Skip cost data
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is True
        
        # Verify cost repository was not called
        cost_repo.get_cost_data.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_analysis_workflow_without_saving_report(self, mock_repositories, mock_analysis_service):
        """Test analysis workflow without saving report."""
        resource_repo, cost_repo, report_repo = mock_repositories
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=mock_analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=False  # Don't save report
        )
        
        result = await use_case.execute(command)
        
        assert result.success is True
        assert result.report_location is None
        
        # Verify report repository was not called
        report_repo.save_report.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_analysis_workflow_with_invalid_command(self, mock_repositories, mock_analysis_service):
        """Test analysis workflow with invalid command parameters."""
        resource_repo, cost_repo, report_repo = mock_repositories
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=mock_analysis_service
        )
        
        # Invalid command - empty regions
        command = AnalyzeResourcesCommand(
            regions=[],  # Invalid empty regions
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is False
        assert "At least one region must be specified" in result.error_message
    
    @pytest.mark.asyncio
    async def test_analysis_workflow_with_repository_failure(self, mock_repositories, mock_analysis_service):
        """Test analysis workflow when repository operations fail."""
        resource_repo, cost_repo, report_repo = mock_repositories
        
        # Make resource repository fail
        resource_repo.get_all_resources = AsyncMock(side_effect=Exception("AWS API Error"))
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=mock_analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is False
        assert "AWS API Error" in result.error_message
    
    @pytest.mark.asyncio
    async def test_analysis_workflow_with_analysis_service_failure(self, mock_repositories, mock_analysis_service):
        """Test analysis workflow when analysis service fails."""
        resource_repo, cost_repo, report_repo = mock_repositories
        
        # Make analysis service fail
        mock_analysis_service.analyze_resources = AsyncMock(side_effect=Exception("Bedrock API Error"))
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=mock_analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is False
        assert "Bedrock API Error" in result.error_message
    
    @pytest.mark.asyncio
    async def test_analysis_workflow_multiple_regions(self, mock_repositories, mock_analysis_service):
        """Test analysis workflow with multiple regions."""
        resource_repo, cost_repo, report_repo = mock_repositories
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=mock_analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1", "us-west-2", "eu-west-1"],  # Multiple regions
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is True
        
        # Verify resource repository was called with all regions
        resource_repo.get_all_resources.assert_called_once_with(["us-east-1", "us-west-2", "eu-west-1"])
    
    @pytest.mark.asyncio
    async def test_analysis_workflow_performance(self, mock_repositories, mock_analysis_service):
        """Test analysis workflow performance with timing."""
        resource_repo, cost_repo, report_repo = mock_repositories
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=mock_analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        # Measure execution time
        start_time = datetime.utcnow()
        result = await use_case.execute(command)
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        assert result.success is True
        assert execution_time < 10.0  # Should complete within 10 seconds with mocks
    
    @pytest.mark.asyncio
    async def test_analysis_workflow_edge_cases(self, mock_repositories, mock_analysis_service):
        """Test analysis workflow with edge cases."""
        resource_repo, cost_repo, report_repo = mock_repositories
        
        # Mock empty resources
        resource_repo.get_all_resources = AsyncMock(return_value=[])
        mock_analysis_service.analyze_resources = AsyncMock(return_value=[])
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=mock_analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        result = await use_case.execute(command)
        
        assert result.success is True
        assert result.report.total_resources_analyzed == 0
        
        # Verify analysis service was still called (even with empty list)
        mock_analysis_service.analyze_resources.assert_called_once_with([])


class TestAnalysisWorkflowConcurrency:
    """Test concurrent analysis scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self):
        """Test handling multiple concurrent analysis requests."""
        # This test would verify that the system can handle multiple
        # analysis requests concurrently without conflicts
        
        # Mock dependencies
        resource_repo = Mock()
        cost_repo = Mock()
        report_repo = Mock()
        analysis_service = Mock()
        
        resource_repo.get_all_resources = AsyncMock(return_value=[])
        cost_repo.get_cost_data = AsyncMock(return_value=CostData(
            total_cost_usd=Decimal('0'),
            period_days=30
        ))
        report_repo.save_report = AsyncMock(return_value="s3://bucket/report.json")
        analysis_service.analyze_resources = AsyncMock(return_value=[])
        analysis_service.generate_report = AsyncMock(return_value=AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="test",
            analysis_period_days=30,
            total_resources_analyzed=0,
            total_monthly_savings_usd=Decimal('0'),
            total_annual_savings_usd=Decimal('0')
        ))
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=resource_repo,
            cost_repository=cost_repo,
            report_repository=report_repo,
            analysis_service=analysis_service
        )
        
        command = AnalyzeResourcesCommand(
            regions=["us-east-1"],
            analysis_period_days=30,
            include_cost_data=True,
            save_report=True
        )
        
        # Run multiple concurrent requests
        tasks = [use_case.execute(command) for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        for result in results:
            assert result.success is True
        
        # Verify repositories were called for each request
        assert resource_repo.get_all_resources.call_count == 5
        assert cost_repo.get_cost_data.call_count == 5
        assert report_repo.save_report.call_count == 5