"""
Use Case: Analyze Resources
Caso de uso principal para análise de recursos e geração de recomendações
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ...domain.entities.resource import Resource, ResourceType
from ...domain.entities.recommendation import (
    Recommendation, 
    RecommendationSummary, 
    ResourceAnalysis,
    SavingsEstimate,
    RecommendationAction,
    ImplementationStep,
    Priority,
    RiskLevel
)
from ...domain.repositories.resource_repository import ResourceRepository
from ...domain.repositories.recommendation_repository import RecommendationRepository
from ...domain.services.analysis_service import (
    AnalysisService,
    PatternAnalyzer,
    CostCalculator,
    RiskAssessment
)
from ...core.exceptions import (
    ResourceNotFoundError,
    AnalysisError,
    ValidationError
)
from ...core.logging import get_logger

logger = get_logger(__name__)


class AnalyzeResourcesUseCase:
    """
    Use Case para análise completa de recursos
    
    Responsabilidades:
    1. Orquestrar coleta de recursos
    2. Executar análise em lote
    3. Gerar recomendações
    4. Persistir resultados
    5. Calcular resumo
    
    Aplica padrões:
    - Command Pattern (encapsula operação)
    - Strategy Pattern (diferentes estratégias de análise)
    - Template Method (fluxo de análise)
    """
    
    def __init__(
        self,
        resource_repository: ResourceRepository,
        recommendation_repository: RecommendationRepository,
        analysis_service: AnalysisService
    ):
        self.resource_repository = resource_repository
        self.recommendation_repository = recommendation_repository
        self.analysis_service = analysis_service
        self.logger = get_logger(self.__class__.__name__)
    
    async def execute(
        self,
        resource_types: Optional[List[ResourceType]] = None,
        regions: Optional[List[str]] = None,
        tags_filter: Optional[Dict[str, str]] = None,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Executa análise completa de recursos
        
        Args:
            resource_types: Tipos de recursos para analisar
            regions: Regiões para filtrar
            tags_filter: Tags para filtrar recursos
            batch_size: Tamanho do lote para processamento
        
        Returns:
            Resultado da análise com resumo e estatísticas
        
        Raises:
            AnalysisError: Erro durante análise
            ValidationError: Parâmetros inválidos
        """
        start_time = datetime.now()
        self.logger.info("Iniciando análise de recursos", extra={
            'resource_types': [rt.value for rt in resource_types] if resource_types else None,
            'regions': regions,
            'tags_filter': tags_filter,
            'batch_size': batch_size
        })
        
        try:
            # 1. Validar parâmetros
            self._validate_parameters(resource_types, regions, batch_size)
            
            # 2. Coletar recursos
            resources = await self._collect_resources(resource_types, regions, tags_filter)
            
            if not resources:
                self.logger.warning("Nenhum recurso encontrado para análise")
                return self._create_empty_result()
            
            self.logger.info(f"Coletados {len(resources)} recursos para análise")
            
            # 3. Processar em lotes
            all_recommendations = []
            for i in range(0, len(resources), batch_size):
                batch = resources[i:i + batch_size]
                batch_recommendations = await self._process_batch(batch, i // batch_size + 1)
                all_recommendations.extend(batch_recommendations)
            
            # 4. Persistir recomendações
            await self._persist_recommendations(all_recommendations)
            
            # 5. Calcular resumo
            summary = await self.analysis_service.calculate_summary(all_recommendations)
            
            # 6. Preparar resultado
            execution_time = (datetime.now() - start_time).total_seconds()
            result = self._create_result(
                resources, 
                all_recommendations, 
                summary, 
                execution_time
            )
            
            self.logger.info("Análise concluída com sucesso", extra={
                'total_resources': len(resources),
                'total_recommendations': len(all_recommendations),
                'execution_time_seconds': execution_time,
                'total_savings_monthly': float(summary.total_monthly_savings_usd)
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro durante análise: {str(e)}", exc_info=True)
            raise AnalysisError(f"Falha na análise de recursos: {str(e)}")
    
    def _validate_parameters(
        self, 
        resource_types: Optional[List[ResourceType]], 
        regions: Optional[List[str]], 
        batch_size: int
    ) -> None:
        """Valida parâmetros de entrada"""
        if batch_size <= 0:
            raise ValidationError("Batch size deve ser positivo")
        
        if batch_size > 100:
            raise ValidationError("Batch size não pode exceder 100")
        
        if regions and any(not region.strip() for region in regions):
            raise ValidationError("Regiões não podem estar vazias")
    
    async def _collect_resources(
        self,
        resource_types: Optional[List[ResourceType]],
        regions: Optional[List[str]],
        tags_filter: Optional[Dict[str, str]]
    ) -> List[Resource]:
        """Coleta recursos baseado nos filtros"""
        try:
            if resource_types:
                # Coletar por tipo específico
                resources = []
                for resource_type in resource_types:
                    type_resources = await self.resource_repository.find_by_type(resource_type)
                    resources.extend(type_resources)
            else:
                # Coletar todos
                resources = await self.resource_repository.find_all()
            
            # Aplicar filtros adicionais
            if regions:
                resources = [r for r in resources if r.region in regions]
            
            if tags_filter:
                resources = [r for r in resources if self._matches_tags(r, tags_filter)]
            
            return resources
            
        except Exception as e:
            raise AnalysisError(f"Erro ao coletar recursos: {str(e)}")
    
    def _matches_tags(self, resource: Resource, tags_filter: Dict[str, str]) -> bool:
        """Verifica se recurso corresponde aos filtros de tags"""
        for key, value in tags_filter.items():
            if key not in resource.tags or resource.tags[key] != value:
                return False
        return True
    
    async def _process_batch(
        self, 
        batch: List[Resource], 
        batch_number: int
    ) -> List[Recommendation]:
        """Processa um lote de recursos"""
        self.logger.info(f"Processando lote {batch_number} com {len(batch)} recursos")
        
        try:
            # Usar análise em lote para eficiência
            recommendations = await self.analysis_service.analyze_resources_batch(batch)
            
            self.logger.info(f"Lote {batch_number} processado: {len(recommendations)} recomendações geradas")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Erro no lote {batch_number}: {str(e)}")
            # Tentar processar individualmente como fallback
            return await self._process_batch_individually(batch, batch_number)
    
    async def _process_batch_individually(
        self, 
        batch: List[Resource], 
        batch_number: int
    ) -> List[Recommendation]:
        """Processa recursos individualmente como fallback"""
        self.logger.warning(f"Processando lote {batch_number} individualmente (fallback)")
        
        recommendations = []
        for resource in batch:
            try:
                analysis = await self.analysis_service.analyze_resource(resource)
                recommendation = await self.analysis_service.generate_recommendation(resource, analysis)
                recommendations.append(recommendation)
            except Exception as e:
                self.logger.error(f"Erro ao processar recurso {resource.resource_id}: {str(e)}")
                continue
        
        return recommendations
    
    async def _persist_recommendations(self, recommendations: List[Recommendation]) -> None:
        """Persiste recomendações no repositório"""
        try:
            # Usar processamento assíncrono para melhor performance
            tasks = [
                self.recommendation_repository.save(recommendation)
                for recommendation in recommendations
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            self.logger.info(f"Persistidas {len(recommendations)} recomendações")
            
        except Exception as e:
            self.logger.error(f"Erro ao persistir recomendações: {str(e)}")
            # Não falhar a análise por erro de persistência
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Cria resultado vazio quando não há recursos"""
        return {
            'status': 'success',
            'message': 'Nenhum recurso encontrado para análise',
            'summary': {
                'total_resources_analyzed': 0,
                'total_monthly_savings_usd': 0.0,
                'total_annual_savings_usd': 0.0,
                'high_priority_actions': 0,
                'medium_priority_actions': 0,
                'low_priority_actions': 0
            },
            'recommendations': [],
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'execution_time_seconds': 0.0
            }
        }
    
    def _create_result(
        self,
        resources: List[Resource],
        recommendations: List[Recommendation],
        summary: RecommendationSummary,
        execution_time: float
    ) -> Dict[str, Any]:
        """Cria resultado final da análise"""
        return {
            'status': 'success',
            'message': f'Análise concluída: {len(resources)} recursos, {len(recommendations)} recomendações',
            'summary': {
                'total_resources_analyzed': summary.total_resources_analyzed,
                'total_monthly_savings_usd': float(summary.total_monthly_savings_usd),
                'total_annual_savings_usd': float(summary.total_annual_savings_usd),
                'high_priority_actions': summary.high_priority_actions,
                'medium_priority_actions': summary.medium_priority_actions,
                'low_priority_actions': summary.low_priority_actions,
                'by_action': summary.by_action,
                'by_resource_type': summary.by_resource_type,
                'average_efficiency_score': summary.average_efficiency_score,
                'total_waste_percentage': summary.total_waste_percentage,
                'priority_distribution': summary.get_priority_distribution(),
                'savings_by_priority': {
                    k: float(v) for k, v in summary.get_savings_by_priority(recommendations).items()
                }
            },
            'recommendations': [rec.to_dict() for rec in recommendations],
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'execution_time_seconds': round(execution_time, 2),
                'batch_processing': True,
                'version': '1.0.0'
            }
        }