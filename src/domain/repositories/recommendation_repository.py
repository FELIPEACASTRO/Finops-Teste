"""
Domain Repository: RecommendationRepository
Interface para persistência de recomendações
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.recommendation import Recommendation, Priority, RiskLevel, RecommendationAction
from ..entities.resource import ResourceType


class RecommendationRepository(ABC):
    """Interface para repositório de recomendações"""
    
    @abstractmethod
    async def save(self, recommendation: Recommendation) -> None:
        """Salva uma recomendação"""
        pass
    
    @abstractmethod
    async def find_by_id(self, recommendation_id: str) -> Optional[Recommendation]:
        """Busca recomendação por ID"""
        pass
    
    @abstractmethod
    async def find_by_resource_id(self, resource_id: str) -> List[Recommendation]:
        """Busca recomendações por ID do recurso"""
        pass
    
    @abstractmethod
    async def find_by_priority(self, priority: Priority) -> List[Recommendation]:
        """Busca recomendações por prioridade"""
        pass
    
    @abstractmethod
    async def find_by_risk_level(self, risk_level: RiskLevel) -> List[Recommendation]:
        """Busca recomendações por nível de risco"""
        pass
    
    @abstractmethod
    async def find_by_action(self, action: RecommendationAction) -> List[Recommendation]:
        """Busca recomendações por ação"""
        pass
    
    @abstractmethod
    async def find_by_resource_type(self, resource_type: ResourceType) -> List[Recommendation]:
        """Busca recomendações por tipo de recurso"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Recommendation]:
        """Retorna todas as recomendações"""
        pass
    
    @abstractmethod
    async def delete(self, recommendation_id: str) -> None:
        """Remove uma recomendação"""
        pass
    
    @abstractmethod
    async def find_by_criteria(
        self,
        resource_type: Optional[ResourceType] = None,
        priority: Optional[Priority] = None,
        risk_level: Optional[RiskLevel] = None,
        action: Optional[RecommendationAction] = None,
        min_savings_usd: Optional[float] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> List[Recommendation]:
        """Busca recomendações por critérios múltiplos"""
        pass
    
    @abstractmethod
    async def get_summary_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas resumidas das recomendações"""
        pass