"""
Entidade de Domínio do Recurso AWS
Representa um recurso AWS com suas métricas e configurações.
Implementa princípios SOLID e Clean Architecture.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from decimal import Decimal


class TipoRecurso(Enum):
    """Tipos de recursos AWS suportados."""
    EC2 = "EC2"
    RDS = "RDS"
    ELB = "ELB"
    LAMBDA = "Lambda"
    EBS = "EBS"
    S3 = "S3"
    DYNAMODB = "DynamoDB"
    ELASTICACHE = "ElastiCache"


class PadraoUso(Enum):
    """Padrões de uso de recursos."""
    CONSTANTE = "constante"
    VARIAVEL = "variavel"
    LOTE = "lote"
    OCIOSO = "ocioso"
    DESCONHECIDO = "desconhecido"


class Prioridade(Enum):
    """Níveis de prioridade das recomendações."""
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class NivelRisco(Enum):
    """Níveis de risco para recomendações."""
    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"


@dataclass
class PontoMetrica:
    """
    Um único ponto de dados de métrica.
    
    Representa um valor de métrica em um momento específico no tempo.
    Segue o princípio da responsabilidade única.
    """
    timestamp: datetime
    valor: float
    
    def para_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "valor": round(self.valor, 2)
        }


@dataclass
class MetricasRecurso:
    """
    Container para métricas de recursos.
    
    Agrupa todas as métricas relacionadas a um recurso AWS.
    Implementa métodos de análise estatística.
    """
    utilizacao_cpu: List[PontoMetrica] = field(default_factory=list)
    utilizacao_memoria: List[PontoMetrica] = field(default_factory=list)
    entrada_rede: List[PontoMetrica] = field(default_factory=list)
    saida_rede: List[PontoMetrica] = field(default_factory=list)
    operacoes_leitura_disco: List[PontoMetrica] = field(default_factory=list)
    operacoes_escrita_disco: List[PontoMetrica] = field(default_factory=list)
    metricas_customizadas: Dict[str, List[PontoMetrica]] = field(default_factory=dict)
    
    def obter_estatisticas_cpu(self) -> Dict[str, float]:
        """
        Calcula estatísticas de CPU.
        
        Returns:
            Dict com média, p95, p99 e máximo de utilização de CPU
        """
        if not self.utilizacao_cpu:
            return {"media": 0.0, "p95": 0.0, "p99": 0.0, "maximo": 0.0}
        
        valores = [dp.valor for dp in self.utilizacao_cpu]
        valores.sort()
        n = len(valores)
        
        return {
            "media": sum(valores) / n,
            "p95": valores[int(0.95 * n)] if n > 0 else 0.0,
            "p99": valores[int(0.99 * n)] if n > 0 else 0.0,
            "maximo": max(valores)
        }
    
    def obter_estatisticas_memoria(self) -> Dict[str, float]:
        """Calcula estatísticas de memória."""
        if not self.utilizacao_memoria:
            return {"media": 0.0, "p95": 0.0, "p99": 0.0, "maximo": 0.0}
        
        valores = [dp.valor for dp in self.utilizacao_memoria]
        valores.sort()
        n = len(valores)
        
        return {
            "media": sum(valores) / n,
            "p95": valores[int(0.95 * n)] if n > 0 else 0.0,
            "p99": valores[int(0.99 * n)] if n > 0 else 0.0,
            "maximo": max(valores)
        }
    
    def calcular_desperdicio_cpu(self) -> float:
        """
        Calcula percentual de desperdício de CPU.
        
        Returns:
            Percentual de desperdício baseado no p95
        """
        stats = self.obter_estatisticas_cpu()
        if stats["p95"] == 0:
            return 0.0
        return max(0.0, 100.0 - stats["p95"])


@dataclass
class RecursoAWS:
    """
    Entidade principal do Recurso AWS.
    
    Esta entidade representa qualquer recurso AWS que pode ser analisado para otimização de custos.
    Segue o Princípio da Responsabilidade Única focando apenas nos dados do recurso.
    """
    id_recurso: str
    tipo_recurso: TipoRecurso
    regiao: str
    id_conta: str
    tags: Dict[str, str] = field(default_factory=dict)
    configuracao: Dict[str, Any] = field(default_factory=dict)
    metricas: MetricasRecurso = field(default_factory=MetricasRecurso)
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
    
    def __post_init__(self):
        """Validação pós-inicialização."""
        if not self.id_recurso:
            raise ValueError("id_recurso não pode estar vazio")
        if not self.regiao:
            raise ValueError("regiao não pode estar vazia")
        if not self.id_conta:
            raise ValueError("id_conta não pode estar vazio")
    
    def obter_tag(self, chave: str, padrao: str = "") -> str:
        """Obtém valor da tag por chave."""
        return self.tags.get(chave, padrao)
    
    def eh_producao(self) -> bool:
        """Verifica se o recurso está em ambiente de produção."""
        env = self.obter_tag("Environment", "").lower()
        return env in ["prod", "production", "prd", "producao"]
    
    def obter_criticidade(self) -> str:
        """Obtém nível de criticidade do recurso."""
        return self.obter_tag("Criticality", "media").lower()
    
    def calcular_score_utilizacao(self) -> float:
        """
        Calcula score de utilização geral do recurso.
        
        Returns:
            Score de 0-100 baseado nas métricas disponíveis
        """
        scores = []
        
        # CPU
        cpu_stats = self.metricas.obter_estatisticas_cpu()
        if cpu_stats["media"] > 0:
            scores.append(cpu_stats["media"])
        
        # Memória
        mem_stats = self.metricas.obter_estatisticas_memoria()
        if mem_stats["media"] > 0:
            scores.append(mem_stats["media"])
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def para_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            "id_recurso": self.id_recurso,
            "tipo_recurso": self.tipo_recurso.value,
            "regiao": self.regiao,
            "id_conta": self.id_conta,
            "tags": self.tags,
            "configuracao": self.configuracao,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
            "metricas": {
                "utilizacao_cpu": [dp.para_dict() for dp in self.metricas.utilizacao_cpu],
                "utilizacao_memoria": [dp.para_dict() for dp in self.metricas.utilizacao_memoria],
                "entrada_rede": [dp.para_dict() for dp in self.metricas.entrada_rede],
                "saida_rede": [dp.para_dict() for dp in self.metricas.saida_rede],
                "operacoes_leitura_disco": [dp.para_dict() for dp in self.metricas.operacoes_leitura_disco],
                "operacoes_escrita_disco": [dp.para_dict() for dp in self.metricas.operacoes_escrita_disco],
                "metricas_customizadas": {
                    k: [dp.para_dict() for dp in v] 
                    for k, v in self.metricas.metricas_customizadas.items()
                }
            }
        }


@dataclass
class DadosCusto:
    """
    Informações de custo para recursos.
    
    Agrega dados de custo e fornece métodos de análise.
    """
    custo_total_usd: Decimal
    periodo_dias: int
    custo_por_servico: Dict[str, Decimal] = field(default_factory=dict)
    custos_diarios: List[Dict[str, Any]] = field(default_factory=list)
    
    def obter_principais_servicos(self, limite: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém principais serviços por custo.
        
        Args:
            limite: Número máximo de serviços a retornar
            
        Returns:
            Lista dos principais serviços ordenados por custo
        """
        servicos_ordenados = sorted(
            self.custo_por_servico.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limite]
        
        return [
            {
                "servico": servico,
                "custo_usd": float(custo),
                "percentual": float(custo / self.custo_total_usd * 100) if self.custo_total_usd > 0 else 0.0
            }
            for servico, custo in servicos_ordenados
        ]
    
    def calcular_custo_medio_diario(self) -> float:
        """Calcula custo médio diário."""
        return float(self.custo_total_usd / self.periodo_dias) if self.periodo_dias > 0 else 0.0
    
    def para_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "custo_total_usd": float(self.custo_total_usd),
            "periodo_dias": self.periodo_dias,
            "custo_medio_diario": self.calcular_custo_medio_diario(),
            "principais_servicos": self.obter_principais_servicos(),
            "custos_diarios": self.custos_diarios
        }


@dataclass
class RecomendacaoOtimizacao:
    """
    Entidade de recomendação de otimização.
    
    Representa uma recomendação específica para otimização de custos.
    Implementa validações de negócio e cálculos de economia.
    """
    id_recurso: str
    tipo_recurso: TipoRecurso
    configuracao_atual: str
    acao_recomendada: str
    detalhes_recomendacao: str
    justificativa: str
    economia_mensal_usd: Decimal
    economia_anual_usd: Decimal
    percentual_economia: float
    nivel_risco: NivelRisco
    prioridade: Prioridade
    passos_implementacao: List[str] = field(default_factory=list)
    padrao_uso: PadraoUso = PadraoUso.DESCONHECIDO
    score_confianca: float = 0.0
    
    def __post_init__(self):
        """Validação pós-inicialização."""
        if self.economia_mensal_usd < 0:
            raise ValueError("economia_mensal_usd não pode ser negativa")
        if not 0 <= self.score_confianca <= 1:
            raise ValueError("score_confianca deve estar entre 0 e 1")
        if not 0 <= self.percentual_economia <= 100:
            raise ValueError("percentual_economia deve estar entre 0 e 100")
    
    def calcular_roi_anual(self, custo_implementacao: Decimal = Decimal('0')) -> float:
        """
        Calcula ROI anual da recomendação.
        
        Args:
            custo_implementacao: Custo para implementar a recomendação
            
        Returns:
            ROI em percentual
        """
        if custo_implementacao <= 0:
            return float('inf') if self.economia_anual_usd > 0 else 0.0
        
        return float((self.economia_anual_usd - custo_implementacao) / custo_implementacao * 100)
    
    def eh_alta_prioridade(self) -> bool:
        """Verifica se é uma recomendação de alta prioridade."""
        return self.prioridade == Prioridade.ALTA
    
    def eh_baixo_risco(self) -> bool:
        """Verifica se é uma recomendação de baixo risco."""
        return self.nivel_risco == NivelRisco.BAIXO
    
    def para_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            "id_recurso": self.id_recurso,
            "tipo_recurso": self.tipo_recurso.value,
            "configuracao_atual": self.configuracao_atual,
            "acao_recomendada": self.acao_recomendada,
            "detalhes_recomendacao": self.detalhes_recomendacao,
            "justificativa": self.justificativa,
            "economia_mensal_usd": float(self.economia_mensal_usd),
            "economia_anual_usd": float(self.economia_anual_usd),
            "percentual_economia": self.percentual_economia,
            "nivel_risco": self.nivel_risco.value,
            "prioridade": self.prioridade.value,
            "passos_implementacao": self.passos_implementacao,
            "padrao_uso": self.padrao_uso.value,
            "score_confianca": self.score_confianca
        }


@dataclass
class RelatorioAnalise:
    """
    Entidade do relatório completo de análise.
    
    Agrega todos os resultados da análise e recomendações.
    Fornece métodos de agregação e análise dos dados.
    """
    gerado_em: datetime
    versao: str
    modelo_usado: str
    periodo_analise_dias: int
    total_recursos_analisados: int
    economia_mensal_total_usd: Decimal
    economia_anual_total_usd: Decimal
    recomendacoes: List[RecomendacaoOtimizacao] = field(default_factory=list)
    dados_custo: Optional[DadosCusto] = None
    
    def obter_recomendacoes_por_prioridade(self, prioridade: Prioridade) -> List[RecomendacaoOtimizacao]:
        """Obtém recomendações filtradas por prioridade."""
        return [r for r in self.recomendacoes if r.prioridade == prioridade]
    
    def contar_alta_prioridade(self) -> int:
        """Obtém contagem de recomendações de alta prioridade."""
        return len(self.obter_recomendacoes_por_prioridade(Prioridade.ALTA))
    
    def contar_media_prioridade(self) -> int:
        """Obtém contagem de recomendações de média prioridade."""
        return len(self.obter_recomendacoes_por_prioridade(Prioridade.MEDIA))
    
    def contar_baixa_prioridade(self) -> int:
        """Obtém contagem de recomendações de baixa prioridade."""
        return len(self.obter_recomendacoes_por_prioridade(Prioridade.BAIXA))
    
    def calcular_roi_medio(self) -> float:
        """Calcula ROI médio de todas as recomendações."""
        if not self.recomendacoes or not self.dados_custo:
            return 0.0
        
        custo_atual_anual = float(self.dados_custo.custo_total_usd * 12 / self.dados_custo.periodo_dias)
        if custo_atual_anual <= 0:
            return 0.0
        
        return float(self.economia_anual_total_usd / custo_atual_anual * 100)
    
    def obter_recomendacoes_por_tipo_recurso(self, tipo: TipoRecurso) -> List[RecomendacaoOtimizacao]:
        """Obtém recomendações filtradas por tipo de recurso."""
        return [r for r in self.recomendacoes if r.tipo_recurso == tipo]
    
    def calcular_economia_por_tipo_recurso(self) -> Dict[str, float]:
        """Calcula economia total por tipo de recurso."""
        economia_por_tipo = {}
        
        for tipo in TipoRecurso:
            recomendacoes_tipo = self.obter_recomendacoes_por_tipo_recurso(tipo)
            economia_total = sum(float(r.economia_mensal_usd) for r in recomendacoes_tipo)
            if economia_total > 0:
                economia_por_tipo[tipo.value] = economia_total
        
        return economia_por_tipo
    
    def para_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            "gerado_em": self.gerado_em.isoformat(),
            "versao": self.versao,
            "modelo_usado": self.modelo_usado,
            "periodo_analise_dias": self.periodo_analise_dias,
            "total_recursos_analisados": self.total_recursos_analisados,
            "economia_mensal_total_usd": float(self.economia_mensal_total_usd),
            "economia_anual_total_usd": float(self.economia_anual_total_usd),
            "roi_medio_percentual": self.calcular_roi_medio(),
            "acoes_alta_prioridade": self.contar_alta_prioridade(),
            "acoes_media_prioridade": self.contar_media_prioridade(),
            "acoes_baixa_prioridade": self.contar_baixa_prioridade(),
            "economia_por_tipo_recurso": self.calcular_economia_por_tipo_recurso(),
            "recomendacoes": [r.para_dict() for r in self.recomendacoes],
            "dados_custo": self.dados_custo.para_dict() if self.dados_custo else None
        }