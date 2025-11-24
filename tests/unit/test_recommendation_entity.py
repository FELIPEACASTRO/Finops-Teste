"""
Testes unitários para entidades de Recommendation
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.domain.entities.recommendation import (
    RecommendationAction,
    SavingsEstimate,
    ResourceAnalysis,
    ImplementationStep,
    Recommendation,
    RecommendationSummary
)
from src.domain.entities.resource import ResourceType, UsagePattern, RiskLevel, Priority


class TestSavingsEstimate:
    """Testes para SavingsEstimate"""
    
    def test_savings_estimate_creation(self):
        """Testa criação de estimativa de economia"""
        savings = SavingsEstimate(
            monthly_usd=Decimal('50.00'),
            annual_usd=Decimal('600.00'),
            percentage=25.0
        )
        
        assert savings.monthly_usd == Decimal('50.00')
        assert savings.annual_usd == Decimal('600.00')
        assert savings.percentage == 25.0
    
    def test_savings_estimate_negative_monthly(self):
        """Testa validação de economia mensal negativa"""
        with pytest.raises(ValueError, match="Monthly savings cannot be negative"):
            SavingsEstimate(
                monthly_usd=Decimal('-10.00'),
                annual_usd=Decimal('-120.00'),
                percentage=0.0
            )
    
    def test_savings_estimate_invalid_percentage(self):
        """Testa validação de percentual inválido"""
        with pytest.raises(ValueError, match="Percentage must be between 0 and 100"):
            SavingsEstimate(
                monthly_usd=Decimal('50.00'),
                annual_usd=Decimal('600.00'),
                percentage=150.0
            )


class TestResourceAnalysis:
    """Testes para ResourceAnalysis"""
    
    def test_resource_analysis_creation(self):
        """Testa criação de análise de recurso"""
        analysis = ResourceAnalysis(
            pattern=UsagePattern.STEADY,
            cpu_mean=25.5,
            cpu_p95=45.2,
            cpu_p99=52.1,
            memory_mean=60.0,
            memory_p95=75.0,
            waste_percentage=54.8
        )
        
        assert analysis.pattern == UsagePattern.STEADY
        assert analysis.cpu_mean == 25.5
        assert analysis.cpu_p95 == 45.2
        assert analysis.waste_percentage == 54.8
        assert analysis.efficiency_score == 45.2  # 100 - 54.8
    
    def test_resource_analysis_efficiency_score_calculation(self):
        """Testa cálculo automático do score de eficiência"""
        analysis = ResourceAnalysis(
            pattern=UsagePattern.VARIABLE,
            cpu_mean=30.0,
            cpu_p95=50.0,
            waste_percentage=30.0
        )
        
        assert analysis.efficiency_score == 70.0  # 100 - 30.0
    
    def test_resource_analysis_custom_efficiency_score(self):
        """Testa score de eficiência customizado"""
        analysis = ResourceAnalysis(
            pattern=UsagePattern.BATCH,
            cpu_mean=15.0,
            cpu_p95=80.0,
            waste_percentage=20.0,
            efficiency_score=85.0
        )
        
        assert analysis.efficiency_score == 85.0  # Valor customizado


class TestImplementationStep:
    """Testes para ImplementationStep"""
    
    def test_implementation_step_creation(self):
        """Testa criação de passo de implementação"""
        step = ImplementationStep(
            order=1,
            description="Criar AMI da instância atual",
            estimated_duration_minutes=15,
            requires_downtime=False,
            automation_possible=True
        )
        
        assert step.order == 1
        assert step.description == "Criar AMI da instância atual"
        assert step.estimated_duration_minutes == 15
        assert step.requires_downtime is False
        assert step.automation_possible is True
    
    def test_implementation_step_invalid_order(self):
        """Testa validação de ordem inválida"""
        with pytest.raises(ValueError, match="Order must be positive"):
            ImplementationStep(
                order=0,
                description="Passo inválido",
                estimated_duration_minutes=10
            )


class TestRecommendation:
    """Testes para Recommendation"""
    
    def create_sample_recommendation(self) -> Recommendation:
        """Cria recomendação de exemplo para testes"""
        analysis = ResourceAnalysis(
            pattern=UsagePattern.STEADY,
            cpu_mean=20.0,
            cpu_p95=30.0,
            waste_percentage=70.0
        )
        
        savings = SavingsEstimate(
            monthly_usd=Decimal('45.50'),
            annual_usd=Decimal('546.00'),
            percentage=50.0
        )
        
        steps = [
            ImplementationStep(1, "Criar AMI", 15, False, True),
            ImplementationStep(2, "Parar instância", 5, True, True),
            ImplementationStep(3, "Modificar tipo", 10, True, True),
            ImplementationStep(4, "Iniciar instância", 5, False, True)
        ]
        
        return Recommendation(
            resource_type=ResourceType.EC2,
            resource_id='i-1234567890abcdef0',
            current_config='t3.large (2 vCPU, 8GB RAM)',
            analysis=analysis,
            action=RecommendationAction.DOWNSIZE,
            details='Downsize de t3.large para t3.medium',
            reasoning='CPU p95 é 30%, indicando 70% de desperdício',
            savings=savings,
            risk_level=RiskLevel.LOW,
            priority=Priority.HIGH,
            implementation_steps=steps
        )
    
    def test_recommendation_creation(self):
        """Testa criação de recomendação"""
        recommendation = self.create_sample_recommendation()
        
        assert recommendation.resource_type == ResourceType.EC2
        assert recommendation.resource_id == 'i-1234567890abcdef0'
        assert recommendation.action == RecommendationAction.DOWNSIZE
        assert recommendation.risk_level == RiskLevel.LOW
        assert recommendation.priority == Priority.HIGH
        assert len(recommendation.implementation_steps) == 4
    
    def test_recommendation_id_generation(self):
        """Testa geração de ID único"""
        rec1 = self.create_sample_recommendation()
        rec2 = self.create_sample_recommendation()
        
        assert rec1.id != rec2.id
        assert rec1.id.startswith('EC2_i-1234567890abcdef0_')
        assert rec2.id.startswith('EC2_i-1234567890abcdef0_')
    
    def test_get_total_implementation_time(self):
        """Testa cálculo de tempo total de implementação"""
        recommendation = self.create_sample_recommendation()
        
        total_time = recommendation.get_total_implementation_time()
        assert total_time == 35  # 15 + 5 + 10 + 5
    
    def test_requires_downtime(self):
        """Testa verificação de necessidade de downtime"""
        recommendation = self.create_sample_recommendation()
        
        assert recommendation.requires_downtime() is True
    
    def test_is_automatable(self):
        """Testa verificação de possibilidade de automação"""
        recommendation = self.create_sample_recommendation()
        
        assert recommendation.is_automatable() is True
    
    def test_get_roi_months(self):
        """Testa cálculo de ROI em meses"""
        recommendation = self.create_sample_recommendation()
        
        # Sem custo de implementação
        roi = recommendation.get_roi_months()
        assert roi == 0.0
        
        # Com custo de implementação
        roi_with_cost = recommendation.get_roi_months(Decimal('91.00'))
        assert roi_with_cost == 2.0  # 91 / 45.5 = 2 meses
    
    def test_get_roi_months_zero_savings(self):
        """Testa ROI com economia zero"""
        recommendation = self.create_sample_recommendation()
        recommendation.savings.monthly_usd = Decimal('0.00')
        
        roi = recommendation.get_roi_months(Decimal('100.00'))
        assert roi == float('inf')
    
    def test_to_dict(self):
        """Testa conversão para dicionário"""
        recommendation = self.create_sample_recommendation()
        
        result = recommendation.to_dict()
        
        assert result['resource_type'] == 'EC2'
        assert result['resource_id'] == 'i-1234567890abcdef0'
        assert result['analysis']['pattern'] == 'steady'
        assert result['analysis']['cpu_mean'] == 20.0
        assert result['recommendation']['action'] == 'downsize'
        assert result['savings']['monthly_usd'] == 45.5
        assert result['risk_level'] == 'low'
        assert result['priority'] == 'high'
        assert len(result['implementation_steps']) == 4
        assert result['metadata']['total_implementation_time_minutes'] == 35
        assert result['metadata']['requires_downtime'] is True
        assert result['metadata']['is_automatable'] is True


class TestRecommendationSummary:
    """Testes para RecommendationSummary"""
    
    def test_recommendation_summary_creation(self):
        """Testa criação de resumo de recomendações"""
        summary = RecommendationSummary(
            total_resources_analyzed=50,
            total_monthly_savings_usd=Decimal('1250.75'),
            total_annual_savings_usd=Decimal('15009.00'),
            high_priority_actions=8,
            medium_priority_actions=15,
            low_priority_actions=12,
            by_action={'downsize': 20, 'delete': 10, 'optimize': 5},
            by_resource_type={'EC2': 25, 'RDS': 10, 'ELB': 5},
            average_efficiency_score=65.5,
            total_waste_percentage=34.5
        )
        
        assert summary.total_resources_analyzed == 50
        assert summary.total_monthly_savings_usd == Decimal('1250.75')
        assert summary.high_priority_actions == 8
        assert summary.by_action['downsize'] == 20
        assert summary.average_efficiency_score == 65.5
    
    def test_get_priority_distribution(self):
        """Testa distribuição percentual por prioridade"""
        summary = RecommendationSummary(
            total_resources_analyzed=100,
            total_monthly_savings_usd=Decimal('1000.00'),
            total_annual_savings_usd=Decimal('12000.00'),
            high_priority_actions=10,
            medium_priority_actions=20,
            low_priority_actions=5,
            by_action={},
            by_resource_type={},
            average_efficiency_score=70.0,
            total_waste_percentage=30.0
        )
        
        distribution = summary.get_priority_distribution()
        
        assert distribution['high'] == 28.6  # 10/35 * 100
        assert distribution['medium'] == 57.1  # 20/35 * 100
        assert distribution['low'] == 14.3  # 5/35 * 100
    
    def test_get_priority_distribution_empty(self):
        """Testa distribuição com zero ações"""
        summary = RecommendationSummary(
            total_resources_analyzed=0,
            total_monthly_savings_usd=Decimal('0.00'),
            total_annual_savings_usd=Decimal('0.00'),
            high_priority_actions=0,
            medium_priority_actions=0,
            low_priority_actions=0,
            by_action={},
            by_resource_type={},
            average_efficiency_score=0.0,
            total_waste_percentage=0.0
        )
        
        distribution = summary.get_priority_distribution()
        
        assert distribution['high'] == 0
        assert distribution['medium'] == 0
        assert distribution['low'] == 0
    
    def test_get_savings_by_priority(self):
        """Testa economia por prioridade"""
        # Criar recomendações de exemplo
        recommendations = []
        
        # Alta prioridade
        for i in range(2):
            rec = Recommendation(
                resource_type=ResourceType.EC2,
                resource_id=f'i-high-{i}',
                current_config='t3.large',
                analysis=ResourceAnalysis(UsagePattern.STEADY, 20.0, 30.0),
                action=RecommendationAction.DOWNSIZE,
                details='Downsize',
                reasoning='Test',
                savings=SavingsEstimate(Decimal('50.00'), Decimal('600.00'), 50.0),
                risk_level=RiskLevel.LOW,
                priority=Priority.HIGH,
                implementation_steps=[]
            )
            recommendations.append(rec)
        
        # Média prioridade
        rec_medium = Recommendation(
            resource_type=ResourceType.RDS,
            resource_id='db-medium',
            current_config='db.t3.medium',
            analysis=ResourceAnalysis(UsagePattern.VARIABLE, 40.0, 60.0),
            action=RecommendationAction.OPTIMIZE,
            details='Optimize',
            reasoning='Test',
            savings=SavingsEstimate(Decimal('25.00'), Decimal('300.00'), 25.0),
            risk_level=RiskLevel.MEDIUM,
            priority=Priority.MEDIUM,
            implementation_steps=[]
        )
        recommendations.append(rec_medium)
        
        summary = RecommendationSummary(
            total_resources_analyzed=3,
            total_monthly_savings_usd=Decimal('125.00'),
            total_annual_savings_usd=Decimal('1500.00'),
            high_priority_actions=2,
            medium_priority_actions=1,
            low_priority_actions=0,
            by_action={},
            by_resource_type={},
            average_efficiency_score=70.0,
            total_waste_percentage=30.0
        )
        
        savings_by_priority = summary.get_savings_by_priority(recommendations)
        
        assert savings_by_priority['high'] == Decimal('100.00')  # 2 * 50.00
        assert savings_by_priority['medium'] == Decimal('25.00')
        assert savings_by_priority['low'] == Decimal('0.00')


if __name__ == '__main__':
    pytest.main([__file__])