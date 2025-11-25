"""
Domain Repository: ResourceRepository
Interface para persistência de recursos
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.resource import Resource, ResourceType


class ResourceRepository(ABC):
    """Interface para repositório de recursos"""
    
    @abstractmethod
    async def save(self, resource: Resource) -> None:
        """Salva um recurso"""
        pass
    
    @abstractmethod
    async def find_by_id(self, resource_id: str) -> Optional[Resource]:
        """Busca recurso por ID"""
        pass
    
    @abstractmethod
    async def find_by_type(self, resource_type: ResourceType) -> List[Resource]:
        """Busca recursos por tipo"""
        pass
    
    @abstractmethod
    async def find_by_region(self, region: str) -> List[Resource]:
        """Busca recursos por região"""
        pass
    
    @abstractmethod
    async def find_by_tags(self, tags: Dict[str, str]) -> List[Resource]:
        """Busca recursos por tags"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Resource]:
        """Retorna todos os recursos"""
        pass
    
    @abstractmethod
    async def delete(self, resource_id: str) -> None:
        """Remove um recurso"""
        pass
    
    @abstractmethod
    async def find_by_criteria(
        self,
        resource_type: Optional[ResourceType] = None,
        region: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> List[Resource]:
        """Busca recursos por critérios múltiplos"""
        pass