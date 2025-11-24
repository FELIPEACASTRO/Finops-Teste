"""
Repository interfaces for resource data access.
Following the Repository Pattern and Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities import AWSResource, CostData, ResourceType


class IResourceRepository(ABC):
    """
    Interface for resource data access.
    
    This interface follows the Dependency Inversion Principle by defining
    abstractions that concrete implementations must follow.
    """

    @abstractmethod
    async def get_resources_by_type(self, resource_type: ResourceType, region: str) -> List[AWSResource]:
        """Get all resources of a specific type in a region."""
        pass

    @abstractmethod
    async def get_resource_by_id(self, resource_id: str) -> Optional[AWSResource]:
        """Get a specific resource by ID."""
        pass

    @abstractmethod
    async def get_resource_metrics(
        self, 
        resource_id: str, 
        resource_type: ResourceType,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get metrics for a specific resource."""
        pass

    @abstractmethod
    async def get_all_resources(self, regions: List[str]) -> List[AWSResource]:
        """Get all resources across specified regions."""
        pass


class ICostRepository(ABC):
    """
    Interface for cost data access.
    
    Separates cost concerns from resource concerns following SRP.
    """

    @abstractmethod
    async def get_cost_data(self, start_date: datetime, end_date: datetime) -> CostData:
        """Get cost data for the specified period."""
        pass

    @abstractmethod
    async def get_cost_by_service(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, float]:
        """Get costs broken down by AWS service."""
        pass

    @abstractmethod
    async def get_resource_cost(
        self, 
        resource_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Get cost for a specific resource."""
        pass


class IReportRepository(ABC):
    """
    Interface for report persistence.
    
    Handles saving and retrieving analysis reports.
    """

    @abstractmethod
    async def save_report(self, report: Dict[str, Any], report_id: str) -> str:
        """Save analysis report and return the saved location."""
        pass

    @abstractmethod
    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a saved report by ID."""
        pass

    @abstractmethod
    async def list_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent reports."""
        pass