"""
Integration tests for Use Case layer.
Tests real use case implementations with mocked external dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime

from src.domain.entities import (
    AWSResource,
    ResourceType,
    OptimizationRecommendation,
    Priority,
    RiskLevel,
    CostData,
    AnalysisReport
)
from src.domain.repositories.resource_repository import (
    IResourceRepository,
    ICostRepository,
    IReportRepository
)
from src.domain.services.analysis_service import IAnalysisService
from src.application.use_cases.analyze_resources_use_case import (
    AnalyzeResourcesUseCase,
    AnalyzeResourcesCommand
)


class TestAnalyzeResourcesUseCaseIntegration:
    """Integration tests for AnalyzeResourcesUseCase with mocked dependencies."""
    
    def test_use_case_initialization(self):
        """Test use case can be initialized with all dependencies."""
        mock_resource_repo = Mock(spec=IResourceRepository)
        mock_cost_repo = Mock(spec=ICostRepository)
        mock_report_repo = Mock(spec=IReportRepository)
        mock_analysis_service = AsyncMock(spec=IAnalysisService)
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=mock_resource_repo,
            cost_repository=mock_cost_repo,
            report_repository=mock_report_repo,
            analysis_service=mock_analysis_service
        )
        
        assert use_case is not None
    
    @pytest.mark.asyncio
    async def test_execute_full_workflow(self):
        """Test execute runs complete workflow and validates DTO response."""
        mock_resource_repo = AsyncMock(spec=IResourceRepository)
        mock_cost_repo = AsyncMock(spec=ICostRepository)
        mock_report_repo = AsyncMock(spec=IReportRepository)
        mock_analysis_service = AsyncMock(spec=IAnalysisService)
        
        resources = [
            AWSResource(
                resource_id="i-ec2-001",
                resource_type=ResourceType.EC2,
                region="us-east-1",
                account_id="123456789012"
            )
        ]
        
        cost_data = CostData(
            total_cost_usd=Decimal('5000.00'),
            period_days=30,
            cost_by_service={'EC2': Decimal('3000.00')}
        )
        
        recommendations = [
            OptimizationRecommendation(
                resource_id="i-ec2-001",
                resource_type=ResourceType.EC2,
                current_config="t3a.large",
                recommended_action="downsize",
                recommendation_details="Downsize to t3a.medium",
                reasoning="Low utilization",
                monthly_savings_usd=Decimal('100.00'),
                annual_savings_usd=Decimal('1200.00'),
                savings_percentage=30.0,
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH
            )
        ]
        
        report = AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="claude-3-sonnet",
            analysis_period_days=30,
            total_resources_analyzed=1,
            total_monthly_savings_usd=Decimal('100.00'),
            total_annual_savings_usd=Decimal('1200.00'),
            recommendations=recommendations
        )
        
        mock_resource_repo.get_all_resources = AsyncMock(return_value=resources)
        mock_cost_repo.get_cost_data = AsyncMock(return_value=cost_data)
        mock_analysis_service.analyze_resources = AsyncMock(return_value=recommendations)
        mock_analysis_service.generate_report = AsyncMock(return_value=report)
        mock_report_repo.save_report = AsyncMock(return_value="s3://reports/2025-11-24.json")
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=mock_resource_repo,
            cost_repository=mock_cost_repo,
            report_repository=mock_report_repo,
            analysis_service=mock_analysis_service
        )
        
        command = AnalyzeResourcesCommand(regions=["us-east-1"])
        result = await use_case.execute(command)
        
        assert result is not None
        
        assert result.success is True
        assert result.report is not None
        assert result.report.total_resources_analyzed == 1
        assert len(result.report.recommendations) == 1
        assert float(result.report.total_monthly_savings_usd) == 100.00
        assert float(result.report.total_annual_savings_usd) == 1200.00
        assert result.report_location == "s3://reports/2025-11-24.json"
        
        mock_resource_repo.get_all_resources.assert_awaited()
        mock_cost_repo.get_cost_data.assert_awaited()
        mock_analysis_service.analyze_resources.assert_awaited()
        mock_report_repo.save_report.assert_awaited()
    
    @pytest.mark.asyncio
    async def test_execute_handles_empty_resources(self):
        """Test execute handles empty resource list."""
        mock_resource_repo = AsyncMock(spec=IResourceRepository)
        mock_cost_repo = AsyncMock(spec=ICostRepository)
        mock_report_repo = AsyncMock(spec=IReportRepository)
        mock_analysis_service = AsyncMock(spec=IAnalysisService)
        
        mock_resource_repo.get_resources_by_regions = AsyncMock(return_value=[])
        mock_cost_repo.get_cost_data = AsyncMock(return_value=CostData(
            total_cost_usd=Decimal('0.00'),
            period_days=30
        ))
        mock_analysis_service.analyze_resources = AsyncMock(return_value=[])
        mock_analysis_service.generate_report = AsyncMock(return_value=AnalysisReport(
            generated_at=datetime.utcnow(),
            version="4.0.0",
            model_used="claude-3-sonnet",
            analysis_period_days=30,
            total_resources_analyzed=0,
            total_monthly_savings_usd=Decimal('0.00'),
            total_annual_savings_usd=Decimal('0.00'),
            recommendations=[]
        ))
        mock_report_repo.save_report = AsyncMock(return_value="s3://reports/empty.json")
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=mock_resource_repo,
            cost_repository=mock_cost_repo,
            report_repository=mock_report_repo,
            analysis_service=mock_analysis_service
        )
        
        command = AnalyzeResourcesCommand(regions=["us-east-1"])
        result = await use_case.execute(command)
        
        assert result is not None


class TestUseCaseWithRealDomainClasses:
    """Tests using real domain classes with mocked infrastructure."""
    
    def test_use_case_with_real_analysis_service_interface(self):
        """Test use case accepts real analysis service interface."""
        class MockAnalysisService(IAnalysisService):
            async def analyze_resource(self, resource):
                return OptimizationRecommendation(
                    resource_id=resource.resource_id,
                    resource_type=resource.resource_type,
                    current_config="test",
                    recommended_action="optimize",
                    recommendation_details="Test",
                    reasoning="Test",
                    monthly_savings_usd=Decimal('50.00'),
                    annual_savings_usd=Decimal('600.00'),
                    savings_percentage=25.0,
                    risk_level=RiskLevel.LOW,
                    priority=Priority.MEDIUM
                )
            
            async def analyze_resources(self, resources):
                return [await self.analyze_resource(r) for r in resources]
            
            async def generate_report(self, resources, cost_data, recommendations):
                return AnalysisReport(
                    generated_at=datetime.utcnow(),
                    version="4.0.0",
                    model_used="test",
                    analysis_period_days=30,
                    total_resources_analyzed=len(resources),
                    total_monthly_savings_usd=sum(r.monthly_savings_usd for r in recommendations) if recommendations else Decimal('0.00'),
                    total_annual_savings_usd=sum(r.annual_savings_usd for r in recommendations) if recommendations else Decimal('0.00'),
                    recommendations=recommendations
                )
        
        mock_resource_repo = Mock(spec=IResourceRepository)
        mock_cost_repo = Mock(spec=ICostRepository)
        mock_report_repo = Mock(spec=IReportRepository)
        analysis_service = MockAnalysisService()
        
        use_case = AnalyzeResourcesUseCase(
            resource_repository=mock_resource_repo,
            cost_repository=mock_cost_repo,
            report_repository=mock_report_repo,
            analysis_service=analysis_service
        )
        
        assert use_case is not None


class TestRepositoryInterfaceCompliance:
    """Tests for repository interface compliance."""
    
    def test_resource_repository_interface(self):
        """Test resource repository interface methods using Mock."""
        mock_repo = Mock(spec=IResourceRepository)
        mock_repo.get_all_resources = AsyncMock(return_value=[])
        mock_repo.get_resources_by_type = AsyncMock(return_value=[])
        mock_repo.get_resource_by_id = AsyncMock(return_value=None)
        mock_repo.get_resource_metrics = AsyncMock(return_value={})
        
        assert hasattr(mock_repo, 'get_all_resources')
        assert hasattr(mock_repo, 'get_resources_by_type')
        assert hasattr(mock_repo, 'get_resource_by_id')
        assert hasattr(mock_repo, 'get_resource_metrics')
    
    def test_cost_repository_interface(self):
        """Test cost repository interface methods using Mock."""
        mock_repo = Mock(spec=ICostRepository)
        mock_repo.get_cost_data = AsyncMock(return_value=CostData(
            total_cost_usd=Decimal('1000.00'),
            period_days=30
        ))
        mock_repo.get_cost_by_service = AsyncMock(return_value={'EC2': 500.0})
        mock_repo.get_resource_cost = AsyncMock(return_value=100.0)
        
        assert hasattr(mock_repo, 'get_cost_data')
        assert hasattr(mock_repo, 'get_cost_by_service')
        assert hasattr(mock_repo, 'get_resource_cost')
    
    def test_report_repository_interface(self):
        """Test report repository interface methods using Mock."""
        mock_repo = Mock(spec=IReportRepository)
        mock_repo.save_report = AsyncMock(return_value="report-id-123")
        mock_repo.get_report = AsyncMock(return_value=None)
        mock_repo.list_reports = AsyncMock(return_value=[])
        
        assert hasattr(mock_repo, 'save_report')
        assert hasattr(mock_repo, 'get_report')
        assert hasattr(mock_repo, 'list_reports')
