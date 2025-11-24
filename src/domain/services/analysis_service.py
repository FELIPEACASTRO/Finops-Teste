"""
Domain Service: AnalysisService
Serviço de domínio para análise de recursos e geração de recomendações
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from decimal import Decimal

from ..entities.resource import Resource, UsagePattern
from ..entities.recommendation import (
    Recommendation, 
    ResourceAnalysis, 
    RecommendationSummary,
    SavingsEstimate,
    RecommendationAction,
    Priority,
    RiskLevel
)


class AnalysisService(ABC):
    """Interface para serviço de análise"""
    
    @abstractmethod
    async def analyze_resource(self, resource: Resource) -> ResourceAnalysis:
        """Analisa um recurso individual"""
        pass
    
    @abstractmethod
    async def generate_recommendation(
        self, 
        resource: Resource, 
        analysis: ResourceAnalysis
    ) -> Recommendation:
        """Gera recomendação baseada na análise"""
        pass
    
    @abstractmethod
    async def analyze_resources_batch(self, resources: List[Resource]) -> List[Recommendation]:
        """Analisa múltiplos recursos em lote"""
        pass
    
    @abstractmethod
    async def calculate_summary(self, recommendations: List[Recommendation]) -> RecommendationSummary:
        """Calcula resumo das recomendações"""
        pass


class PatternAnalyzer:
    """Analisador de padrões de uso - Classe utilitária"""
    
    @staticmethod
    def identify_usage_pattern(cpu_values: List[float]) -> UsagePattern:
        """
        Identifica padrão de uso baseado nos valores de CPU
        
        Algoritmo de análise de padrões:
        - Steady: Baixa variabilidade (CV < 0.3)
        - Variable: Alta variabilidade (CV >= 0.3)
        - Batch: Picos esporádicos
        - Idle: Uso muito baixo (média < 5%)
        
        Complexidade: O(n) onde n é o número de valores
        """
        if not cpu_values:
            return UsagePattern.UNKNOWN
        
        mean_cpu = sum(cpu_values) / len(cpu_values)
        
        # Idle: uso muito baixo
        if mean_cpu < 5.0:
            return UsagePattern.IDLE
        
        # Calcular coeficiente de variação
        if mean_cpu == 0:
            return UsagePattern.IDLE
        
        variance = sum((x - mean_cpu) ** 2 for x in cpu_values) / len(cpu_values)
        std_dev = variance ** 0.5
        cv = std_dev / mean_cpu
        
        # Detectar padrão batch (picos esporádicos)
        max_cpu = max(cpu_values)
        if max_cpu > 80 and mean_cpu < 30:
            return UsagePattern.BATCH
        
        # Steady vs Variable baseado no coeficiente de variação
        return UsagePattern.STEADY if cv < 0.3 else UsagePattern.VARIABLE
    
    @staticmethod
    def calculate_waste_percentage(cpu_mean: float, cpu_p95: float) -> float:
        """
        Calcula percentual de desperdício baseado na utilização
        
        Fórmula: waste = max(0, 100 - cpu_p95)
        Considera que o P95 representa a utilização real necessária
        """
        return max(0.0, 100.0 - cpu_p95)
    
    @staticmethod
    def calculate_efficiency_score(
        cpu_mean: float, 
        cpu_p95: float, 
        pattern: UsagePattern
    ) -> float:
        """
        Calcula score de eficiência (0-100)
        
        Considera:
        - Utilização média
        - Padrão de uso
        - Desperdício
        """
        base_score = min(cpu_p95, 100.0)
        
        # Ajustes por padrão
        pattern_multipliers = {
            UsagePattern.STEADY: 1.0,
            UsagePattern.VARIABLE: 0.9,
            UsagePattern.BATCH: 0.8,
            UsagePattern.IDLE: 0.1,
            UsagePattern.UNKNOWN: 0.5
        }
        
        multiplier = pattern_multipliers.get(pattern, 0.5)
        return round(base_score * multiplier, 1)


class CostCalculator:
    """Calculadora de custos - Classe utilitária"""
    
    # Preços base por hora (us-east-1) - Simplificado para exemplo
    EC2_PRICING = {
        't3.nano': 0.0052, 't3.micro': 0.0104, 't3.small': 0.0208,
        't3.medium': 0.0416, 't3.large': 0.0832, 't3.xlarge': 0.1664,
        't3a.nano': 0.0047, 't3a.micro': 0.0094, 't3a.small': 0.0188,
        't3a.medium': 0.0376, 't3a.large': 0.0752, 't3a.xlarge': 0.1504,
        'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384,
        'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34
    }
    
    RDS_PRICING = {
        'db.t3.micro': 0.017, 'db.t3.small': 0.034, 'db.t3.medium': 0.068,
        'db.t3.large': 0.136, 'db.t3.xlarge': 0.272,
        'db.m5.large': 0.192, 'db.m5.xlarge': 0.384, 'db.m5.2xlarge': 0.768
    }
    
    @classmethod
    def calculate_ec2_monthly_cost(cls, instance_type: str) -> Decimal:
        """Calcula custo mensal de instância EC2"""
        hourly_cost = cls.EC2_PRICING.get(instance_type, 0.1)  # Default fallback
        monthly_cost = hourly_cost * 24 * 30  # 30 dias
        return Decimal(str(round(monthly_cost, 2)))
    
    @classmethod
    def calculate_rds_monthly_cost(cls, instance_class: str) -> Decimal:
        """Calcula custo mensal de instância RDS"""
        hourly_cost = cls.RDS_PRICING.get(instance_class, 0.1)  # Default fallback
        monthly_cost = hourly_cost * 24 * 30  # 30 dias
        return Decimal(str(round(monthly_cost, 2)))
    
    @classmethod
    def calculate_savings(
        cls, 
        current_cost: Decimal, 
        new_cost: Decimal
    ) -> SavingsEstimate:
        """Calcula estimativa de economia"""
        monthly_savings = current_cost - new_cost
        annual_savings = monthly_savings * 12
        
        if current_cost > 0:
            percentage = float(monthly_savings / current_cost * 100)
        else:
            percentage = 0.0
        
        return SavingsEstimate(
            monthly_usd=monthly_savings,
            annual_usd=annual_savings,
            percentage=round(percentage, 1)
        )


class RiskAssessment:
    """Avaliador de riscos - Classe utilitária"""
    
    @staticmethod
    def assess_risk(
        resource: Resource,
        action: RecommendationAction,
        current_utilization: float,
        target_utilization: float
    ) -> RiskLevel:
        """
        Avalia nível de risco de uma recomendação
        
        Considera:
        - Tipo de ação
        - Ambiente (produção = maior risco)
        - Criticidade
        - Utilização atual vs target
        """
        # Fatores de risco base
        risk_score = 0
        
        # Risco por ação
        action_risks = {
            RecommendationAction.DELETE: 10,
            RecommendationAction.DOWNSIZE: 5,
            RecommendationAction.MIGRATE: 7,
            RecommendationAction.UPSIZE: 2,
            RecommendationAction.OPTIMIZE: 3,
            RecommendationAction.SCHEDULE: 4,
            RecommendationAction.NO_CHANGE: 0
        }
        risk_score += action_risks.get(action, 5)
        
        # Risco por ambiente
        if resource.is_production():
            risk_score += 5
        
        # Risco por criticidade
        criticality = resource.get_criticality()
        if criticality == 'high':
            risk_score += 5
        elif criticality == 'medium':
            risk_score += 2
        
        # Risco por utilização target
        if target_utilization > 80:
            risk_score += 3
        elif target_utilization > 60:
            risk_score += 1
        
        # Converter score para nível
        if risk_score <= 5:
            return RiskLevel.LOW
        elif risk_score <= 12:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    @staticmethod
    def assess_priority(
        savings: SavingsEstimate,
        risk_level: RiskLevel,
        efficiency_score: float
    ) -> Priority:
        """
        Avalia prioridade baseada em economia, risco e eficiência
        
        Matriz de decisão:
        - Alta economia + Baixo risco = Alta prioridade
        - Baixa eficiência + Baixo risco = Alta prioridade
        - Alto risco = Prioridade reduzida
        """
        priority_score = 0
        
        # Score por economia mensal
        if savings.monthly_usd >= 100:
            priority_score += 3
        elif savings.monthly_usd >= 50:
            priority_score += 2
        elif savings.monthly_usd >= 10:
            priority_score += 1
        
        # Score por eficiência (quanto menor, maior prioridade)
        if efficiency_score < 30:
            priority_score += 3
        elif efficiency_score < 50:
            priority_score += 2
        elif efficiency_score < 70:
            priority_score += 1
        
        # Penalidade por risco
        if risk_level == RiskLevel.HIGH:
            priority_score -= 2
        elif risk_level == RiskLevel.MEDIUM:
            priority_score -= 1
        
        # Converter para prioridade
        if priority_score >= 4:
            return Priority.HIGH
        elif priority_score >= 2:
            return Priority.MEDIUM
        else:
            return Priority.LOW