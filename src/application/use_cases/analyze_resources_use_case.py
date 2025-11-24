"""
Use case for analyzing AWS resources and generating optimization recommendations.
Orchestrates the analysis workflow following Clean Architecture principles.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

from ...domain.entities import (
    AnalysisReport, 
    AWSResource, 
    OptimizationRecommendation,
    CostData
)
from ...domain.repositories.resource_repository import (
    IResourceRepository, 
    ICostRepository, 
    IReportRepository
)
from ...domain.services.analysis_service import IAnalysisService
from ..dto.analysis_dto import AnalysisRequestDTO, AnalysisResponseDTO


@dataclass
class AnalyzeResourcesCommand:
    """Command for resource analysis request."""
    regions: List[str]
    analysis_period_days: int = 30
    include_cost_data: bool = True
    save_report: bool = True


class AnalyzeResourcesUseCase:
    """
    Use case for analyzing AWS resources.
    
    Orchestrates the entire analysis workflow:
    1. Collect resources from AWS
    2. Collect cost data
    3. Analyze resources using AI/ML
    4. Generate recommendations
    5. Create and save report
    
    Follows the Single Responsibility Principle and Dependency Inversion Principle.
    """

    def __init__(
        self,
        resource_repository: IResourceRepository,
        cost_repository: ICostRepository,
        report_repository: IReportRepository,
        analysis_service: IAnalysisService,
        logger: Optional[logging.Logger] = None
    ):
        self._resource_repository = resource_repository
        self._cost_repository = cost_repository
        self._report_repository = report_repository
        self._analysis_service = analysis_service
        self._logger = logger or logging.getLogger(__name__)

    async def execute(self, command: AnalyzeResourcesCommand) -> AnalysisResponseDTO:
        """
        Execute the resource analysis use case.
        
        Time Complexity: O(n * m) where n is number of resources and m is analysis complexity
        Space Complexity: O(n) where n is number of resources
        
        Args:
            command: Analysis command with parameters
            
        Returns:
            AnalysisResponseDTO: Analysis results
            
        Raises:
            ValueError: If invalid parameters provided
            Exception: If analysis fails
        """
        try:
            self._logger.info(f"Starting resource analysis for regions: {command.regions}")
            
            # Validate input
            self._validate_command(command)
            
            # Step 1: Collect resources
            self._logger.info("Collecting AWS resources...")
            resources = await self._collect_resources(command.regions)
            self._logger.info(f"Collected {len(resources)} resources")
            
            # Step 2: Collect cost data (if requested)
            cost_data = None
            if command.include_cost_data:
                self._logger.info("Collecting cost data...")
                cost_data = await self._collect_cost_data(command.analysis_period_days)
                self._logger.info(f"Collected cost data: ${cost_data.total_cost_usd}")
            
            # Step 3: Analyze resources
            self._logger.info("Analyzing resources...")
            recommendations = await self._analyze_resources(resources)
            self._logger.info(f"Generated {len(recommendations)} recommendations")
            
            # Step 4: Generate report
            self._logger.info("Generating analysis report...")
            report = await self._generate_report(
                resources, 
                recommendations, 
                cost_data, 
                command.analysis_period_days
            )
            
            # Step 5: Save report (if requested)
            report_location = None
            if command.save_report:
                self._logger.info("Saving report...")
                report_id = f"finops-analysis-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
                report_location = await self._report_repository.save_report(
                    report.to_dict(), 
                    report_id
                )
                self._logger.info(f"Report saved to: {report_location}")
            
            self._logger.info("Analysis completed successfully")
            
            return AnalysisResponseDTO(
                success=True,
                report=report,
                report_location=report_location,
                message="Analysis completed successfully"
            )
            
        except Exception as e:
            self._logger.error(f"Analysis failed: {str(e)}")
            return AnalysisResponseDTO(
                success=False,
                error_message=str(e),
                message="Analysis failed"
            )

    def _validate_command(self, command: AnalyzeResourcesCommand) -> None:
        """Validate the analysis command."""
        if not command.regions:
            raise ValueError("At least one region must be specified")
        
        if command.analysis_period_days <= 0 or command.analysis_period_days > 365:
            raise ValueError("Analysis period must be between 1 and 365 days")

    async def _collect_resources(self, regions: List[str]) -> List[AWSResource]:
        """
        Collect all resources from specified regions.
        
        Time Complexity: O(r * s) where r is regions and s is services per region
        Space Complexity: O(n) where n is total resources
        """
        all_resources = []
        
        for region in regions:
            try:
                region_resources = await self._resource_repository.get_all_resources([region])
                all_resources.extend(region_resources)
                self._logger.debug(f"Collected {len(region_resources)} resources from {region}")
            except Exception as e:
                self._logger.warning(f"Failed to collect resources from {region}: {str(e)}")
                # Continue with other regions
                continue
        
        return all_resources

    async def _collect_cost_data(self, period_days: int) -> CostData:
        """
        Collect cost data for the specified period.
        
        Time Complexity: O(1) - single API call
        Space Complexity: O(d) where d is number of days
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        return await self._cost_repository.get_cost_data(start_date, end_date)

    async def _analyze_resources(self, resources: List[AWSResource]) -> List[OptimizationRecommendation]:
        """
        Analyze resources and generate recommendations.
        
        Time Complexity: O(n * a) where n is resources and a is analysis complexity
        Space Complexity: O(n) where n is number of recommendations
        """
        return await self._analysis_service.analyze_resources(resources)

    async def _generate_report(
        self,
        resources: List[AWSResource],
        recommendations: List[OptimizationRecommendation],
        cost_data: Optional[CostData],
        analysis_period_days: int
    ) -> AnalysisReport:
        """
        Generate the final analysis report.
        
        Time Complexity: O(r) where r is number of recommendations
        Space Complexity: O(r) where r is number of recommendations
        """
        return await self._analysis_service.generate_report(
            resources, 
            cost_data, 
            recommendations
        )