"""
Serviço de Análise de Recursos
Implementa a lógica de negócio para análise de recursos AWS.
Segue o padrão Domain Service do DDD.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from decimal import Decimal

from ..entities.recurso import (
    RecursoAWS, 
    RecomendacaoOtimizacao, 
    RelatorioAnalise,
    DadosCusto,
    TipoRecurso,
    Prioridade,
    NivelRisco,
    PadraoUso
)


class IServicoAnaliseIA(ABC):
    """
    Interface para serviços de análise com IA.
    
    Define o contrato para análise inteligente de recursos usando IA.
    Segue o Princípio da Inversão de Dependência.
    """
    
    @abstractmethod
    async def analisar_recursos(
        self, 
        recursos: List[RecursoAWS], 
        dados_custo: DadosCusto
    ) -> List[RecomendacaoOtimizacao]:
        """
        Analisa recursos e retorna recomendações de otimização.
        
        Args:
            recursos: Lista de recursos AWS para análise
            dados_custo: Dados de custo dos recursos
            
        Returns:
            Lista de recomendações de otimização
        """
        pass


class ServicoAnaliseRecursos:
    """
    Serviço de domínio para análise de recursos AWS.
    
    Implementa a lógica de negócio para análise e otimização de recursos.
    Coordena a análise usando diferentes estratégias (Strategy Pattern).
    """
    
    def __init__(self, servico_ia: IServicoAnaliseIA):
        """
        Inicializa o serviço de análise.
        
        Args:
            servico_ia: Serviço de análise com IA
        """
        self._servico_ia = servico_ia
    
    async def analisar_recursos_completo(
        self, 
        recursos: List[RecursoAWS], 
        dados_custo: DadosCusto,
        versao: str,
        modelo_usado: str
    ) -> RelatorioAnalise:
        """
        Realiza análise completa dos recursos.
        
        Args:
            recursos: Lista de recursos para análise
            dados_custo: Dados de custo
            versao: Versão do analisador
            modelo_usado: Modelo de IA usado
            
        Returns:
            Relatório completo de análise
        """
        # Análise com IA
        recomendacoes = await self._servico_ia.analisar_recursos(recursos, dados_custo)
        
        # Aplicar regras de negócio adicionais
        recomendacoes = self._aplicar_regras_negocio(recomendacoes, recursos)
        
        # Calcular totais
        economia_mensal_total = sum(r.economia_mensal_usd for r in recomendacoes)
        economia_anual_total = sum(r.economia_anual_usd for r in recomendacoes)
        
        # Criar relatório
        from datetime import datetime
        relatorio = RelatorioAnalise(
            gerado_em=datetime.now(),
            versao=versao,
            modelo_usado=modelo_usado,
            periodo_analise_dias=dados_custo.periodo_dias,
            total_recursos_analisados=len(recursos),
            economia_mensal_total_usd=economia_mensal_total,
            economia_anual_total_usd=economia_anual_total,
            recomendacoes=recomendacoes,
            dados_custo=dados_custo
        )
        
        return relatorio
    
    def _aplicar_regras_negocio(
        self, 
        recomendacoes: List[RecomendacaoOtimizacao],
        recursos: List[RecursoAWS]
    ) -> List[RecomendacaoOtimizacao]:
        """
        Aplica regras de negócio específicas às recomendações.
        
        Args:
            recomendacoes: Lista de recomendações da IA
            recursos: Lista de recursos originais
            
        Returns:
            Lista de recomendações ajustadas
        """
        recursos_dict = {r.id_recurso: r for r in recursos}
        recomendacoes_ajustadas = []
        
        for rec in recomendacoes:
            recurso = recursos_dict.get(rec.id_recurso)
            if not recurso:
                continue
            
            # Regra 1: Recursos de produção têm risco aumentado
            if recurso.eh_producao() and rec.nivel_risco == NivelRisco.BAIXO:
                rec.nivel_risco = NivelRisco.MEDIO
            
            # Regra 2: Recursos críticos têm prioridade aumentada
            if recurso.obter_criticidade() == "alta" and rec.prioridade == Prioridade.BAIXA:
                rec.prioridade = Prioridade.MEDIA
            
            # Regra 3: Economia muito baixa tem prioridade reduzida
            if rec.economia_mensal_usd < Decimal('10') and rec.prioridade == Prioridade.ALTA:
                rec.prioridade = Prioridade.BAIXA
            
            # Regra 4: Validar score de confiança
            if rec.score_confianca < 0.5 and rec.prioridade == Prioridade.ALTA:
                rec.prioridade = Prioridade.MEDIA
                rec.nivel_risco = NivelRisco.ALTO
            
            recomendacoes_ajustadas.append(rec)
        
        return recomendacoes_ajustadas
    
    def calcular_metricas_recursos(self, recursos: List[RecursoAWS]) -> Dict[str, Any]:
        """
        Calcula métricas agregadas dos recursos.
        
        Args:
            recursos: Lista de recursos
            
        Returns:
            Dicionário com métricas calculadas
        """
        if not recursos:
            return {}
        
        # Contagem por tipo
        contagem_por_tipo = {}
        utilizacao_media_por_tipo = {}
        
        for recurso in recursos:
            tipo = recurso.tipo_recurso.value
            contagem_por_tipo[tipo] = contagem_por_tipo.get(tipo, 0) + 1
            
            # Calcular utilização média
            score_utilizacao = recurso.calcular_score_utilizacao()
            if tipo not in utilizacao_media_por_tipo:
                utilizacao_media_por_tipo[tipo] = []
            utilizacao_media_por_tipo[tipo].append(score_utilizacao)
        
        # Calcular médias
        for tipo in utilizacao_media_por_tipo:
            scores = utilizacao_media_por_tipo[tipo]
            utilizacao_media_por_tipo[tipo] = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "total_recursos": len(recursos),
            "contagem_por_tipo": contagem_por_tipo,
            "utilizacao_media_por_tipo": utilizacao_media_por_tipo,
            "recursos_producao": len([r for r in recursos if r.eh_producao()]),
            "recursos_criticos": len([r for r in recursos if r.obter_criticidade() == "alta"])
        }
    
    def identificar_padroes_uso(self, recurso: RecursoAWS) -> PadraoUso:
        """
        Identifica padrão de uso de um recurso baseado em suas métricas.
        
        Args:
            recurso: Recurso para análise
            
        Returns:
            Padrão de uso identificado
        """
        stats_cpu = recurso.metricas.obter_estatisticas_cpu()
        
        if stats_cpu["media"] == 0:
            return PadraoUso.OCIOSO
        
        # Calcular variabilidade
        if stats_cpu["maximo"] > 0:
            coeficiente_variacao = (stats_cpu["maximo"] - stats_cpu["media"]) / stats_cpu["maximo"]
        else:
            coeficiente_variacao = 0
        
        # Classificar padrão
        if coeficiente_variacao < 0.2:
            return PadraoUso.CONSTANTE
        elif coeficiente_variacao < 0.5:
            return PadraoUso.VARIAVEL
        elif stats_cpu["p95"] > stats_cpu["media"] * 3:
            return PadraoUso.LOTE
        else:
            return PadraoUso.VARIAVEL
    
    def calcular_potencial_economia(self, recursos: List[RecursoAWS]) -> Dict[str, float]:
        """
        Calcula potencial de economia por tipo de recurso.
        
        Args:
            recursos: Lista de recursos
            
        Returns:
            Dicionário com potencial de economia por tipo
        """
        potencial_por_tipo = {}
        
        for recurso in recursos:
            tipo = recurso.tipo_recurso.value
            desperdicio_cpu = recurso.metricas.calcular_desperdicio_cpu()
            
            if tipo not in potencial_por_tipo:
                potencial_por_tipo[tipo] = []
            
            potencial_por_tipo[tipo].append(desperdicio_cpu)
        
        # Calcular média de desperdício por tipo
        for tipo in potencial_por_tipo:
            desperdicios = potencial_por_tipo[tipo]
            potencial_por_tipo[tipo] = sum(desperdicios) / len(desperdicios) if desperdicios else 0.0
        
        return potencial_por_tipo