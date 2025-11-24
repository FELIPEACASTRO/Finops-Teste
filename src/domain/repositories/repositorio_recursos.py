"""
Interface do Repositório de Recursos
Define o contrato para acesso aos dados de recursos seguindo o padrão Repository.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.resource import RecursoAWS, TipoRecurso, DadosCusto


class IRepositorioRecursos(ABC):
    """
    Interface para acesso aos dados de recursos.
    
    Esta interface segue o Princípio da Inversão de Dependência definindo
    abstrações que as implementações concretas devem seguir.
    """
    
    @abstractmethod
    async def obter_recursos_ec2(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todas as instâncias EC2 de uma região."""
        pass
    
    @abstractmethod
    async def obter_recursos_rds(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todas as instâncias RDS de uma região."""
        pass
    
    @abstractmethod
    async def obter_recursos_elb(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todos os Load Balancers de uma região."""
        pass
    
    @abstractmethod
    async def obter_recursos_lambda(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todas as funções Lambda de uma região."""
        pass
    
    @abstractmethod
    async def obter_recursos_ebs(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todos os volumes EBS de uma região."""
        pass
    
    @abstractmethod
    async def obter_recursos_s3(self) -> List[RecursoAWS]:
        """Obtém todos os buckets S3 (serviço global)."""
        pass
    
    @abstractmethod
    async def obter_recursos_dynamodb(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todas as tabelas DynamoDB de uma região."""
        pass
    
    @abstractmethod
    async def obter_recursos_elasticache(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todos os clusters ElastiCache de uma região."""
        pass
    
    @abstractmethod
    async def obter_dados_custo(self, dias: int) -> DadosCusto:
        """Obtém dados de custo para o número especificado de dias."""
        pass


class IRepositorioMetricas(ABC):
    """Interface para acesso às métricas do CloudWatch."""
    
    @abstractmethod
    async def obter_utilizacao_cpu(
        self, 
        tipo_recurso: TipoRecurso, 
        id_recurso: str, 
        inicio: datetime, 
        fim: datetime
    ) -> List[Dict[str, Any]]:
        """Obtém métricas de utilização de CPU."""
        pass
    
    @abstractmethod
    async def obter_utilizacao_memoria(
        self, 
        tipo_recurso: TipoRecurso, 
        id_recurso: str, 
        inicio: datetime, 
        fim: datetime
    ) -> List[Dict[str, Any]]:
        """Obtém métricas de utilização de memória."""
        pass
    
    @abstractmethod
    async def obter_metricas_rede(
        self, 
        tipo_recurso: TipoRecurso, 
        id_recurso: str, 
        inicio: datetime, 
        fim: datetime
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Obtém métricas de entrada/saída de rede."""
        pass
    
    @abstractmethod
    async def obter_metricas_disco(
        self, 
        tipo_recurso: TipoRecurso, 
        id_recurso: str, 
        inicio: datetime, 
        fim: datetime
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Obtém métricas de leitura/escrita de disco."""
        pass
    
    @abstractmethod
    async def obter_metricas_customizadas(
        self, 
        namespace: str,
        nome_metrica: str,
        dimensoes: List[Dict[str, str]], 
        inicio: datetime, 
        fim: datetime
    ) -> List[Dict[str, Any]]:
        """Obtém métricas customizadas do CloudWatch."""
        pass