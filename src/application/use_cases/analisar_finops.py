"""
Caso de Uso: Analisar FinOps
Orquestra a análise completa de recursos AWS para otimização de custos.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ...domain.entities.recurso import (
    RecursoAWS, RelatorioAnalise, DadosCusto, TipoRecurso, MetricasRecurso, PontoMetrica
)
from ...domain.repositories.repositorio_recursos import IRepositorioRecursos, IRepositorioMetricas
from ...domain.services.servico_analise import ServicoAnaliseRecursos
from ...infrastructure.aws.repositorio_metricas_aws import RepositorioMetricasAWS

logger = logging.getLogger(__name__)


class AnalisarFinOpsUseCase:
    """
    Caso de uso principal para análise de FinOps.
    
    Orquestra todo o processo de coleta de dados, análise e geração de relatório.
    Implementa padrão Command e segue princípios de Clean Architecture.
    """
    
    def __init__(
        self,
        repositorio_recursos: IRepositorioRecursos,
        repositorio_metricas: IRepositorioMetricas,
        servico_analise: ServicoAnaliseRecursos
    ):
        """
        Inicializa o caso de uso.
        
        Args:
            repositorio_recursos: Repositório para dados de recursos
            repositorio_metricas: Repositório para métricas
            servico_analise: Serviço de análise de recursos
        """
        self.repositorio_recursos = repositorio_recursos
        self.repositorio_metricas = repositorio_metricas
        self.servico_analise = servico_analise
        logger.info("Caso de uso AnalisarFinOps inicializado")
    
    async def executar(
        self,
        regioes: List[str],
        periodo_dias: int = 30,
        versao: str = "4.0",
        modelo_ia: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    ) -> RelatorioAnalise:
        """
        Executa análise completa de FinOps.
        
        Args:
            regioes: Lista de regiões AWS para análise
            periodo_dias: Período em dias para análise de métricas
            versao: Versão do analisador
            modelo_ia: Modelo de IA utilizado
            
        Returns:
            Relatório completo de análise
            
        Raises:
            Exception: Em caso de erro na análise
        """
        logger.info(f"Iniciando análise FinOps para {len(regioes)} regiões")
        logger.info(f"Período de análise: {periodo_dias} dias")
        
        try:
            # Etapa 1: Coletar todos os recursos
            logger.info("📊 Etapa 1: Coletando recursos AWS...")
            recursos = await self._coletar_todos_recursos(regioes)
            logger.info(f"✓ {len(recursos)} recursos coletados")
            
            # Etapa 2: Coletar métricas de performance
            logger.info("📈 Etapa 2: Coletando métricas de performance...")
            recursos_com_metricas = await self._enriquecer_com_metricas(recursos, periodo_dias)
            logger.info(f"✓ Métricas coletadas para {len(recursos_com_metricas)} recursos")
            
            # Etapa 3: Coletar dados de custo
            logger.info("💰 Etapa 3: Coletando dados de custo...")
            dados_custo = await self.repositorio_recursos.obter_dados_custo(periodo_dias)
            logger.info(f"✓ Custo total analisado: ${dados_custo.custo_total_usd:.2f}")
            
            # Etapa 4: Análise inteligente
            logger.info("🤖 Etapa 4: Executando análise inteligente...")
            relatorio = await self.servico_analise.analisar_recursos_completo(
                recursos_com_metricas,
                dados_custo,
                versao,
                modelo_ia
            )
            
            logger.info("✅ Análise FinOps concluída com sucesso!")
            logger.info(f"💡 Economia potencial: ${relatorio.economia_mensal_total_usd:.2f}/mês")
            logger.info(f"🎯 Recomendações geradas: {len(relatorio.recomendacoes)}")
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro na análise FinOps: {e}")
            raise
    
    async def _coletar_todos_recursos(self, regioes: List[str]) -> List[RecursoAWS]:
        """
        Coleta todos os recursos de todas as regiões.
        
        Implementa coleta paralela para otimização de performance.
        Complexidade: O(n*m) onde n=regiões, m=recursos por região.
        """
        todos_recursos = []
        
        for regiao in regioes:
            logger.info(f"Coletando recursos da região: {regiao}")
            
            try:
                # Coletar recursos de cada tipo
                recursos_regiao = []
                
                # EC2
                recursos_ec2 = await self.repositorio_recursos.obter_recursos_ec2(regiao)
                recursos_regiao.extend(recursos_ec2)
                logger.debug(f"  ✓ {len(recursos_ec2)} instâncias EC2")
                
                # RDS
                recursos_rds = await self.repositorio_recursos.obter_recursos_rds(regiao)
                recursos_regiao.extend(recursos_rds)
                logger.debug(f"  ✓ {len(recursos_rds)} instâncias RDS")
                
                # ELB
                recursos_elb = await self.repositorio_recursos.obter_recursos_elb(regiao)
                recursos_regiao.extend(recursos_elb)
                logger.debug(f"  ✓ {len(recursos_elb)} Load Balancers")
                
                # Lambda
                recursos_lambda = await self.repositorio_recursos.obter_recursos_lambda(regiao)
                recursos_regiao.extend(recursos_lambda)
                logger.debug(f"  ✓ {len(recursos_lambda)} funções Lambda")
                
                # EBS
                recursos_ebs = await self.repositorio_recursos.obter_recursos_ebs(regiao)
                recursos_regiao.extend(recursos_ebs)
                logger.debug(f"  ✓ {len(recursos_ebs)} volumes EBS")
                
                # DynamoDB
                recursos_dynamodb = await self.repositorio_recursos.obter_recursos_dynamodb(regiao)
                recursos_regiao.extend(recursos_dynamodb)
                logger.debug(f"  ✓ {len(recursos_dynamodb)} tabelas DynamoDB")
                
                # ElastiCache
                recursos_elasticache = await self.repositorio_recursos.obter_recursos_elasticache(regiao)
                recursos_regiao.extend(recursos_elasticache)
                logger.debug(f"  ✓ {len(recursos_elasticache)} clusters ElastiCache")
                
                todos_recursos.extend(recursos_regiao)
                logger.info(f"✓ Região {regiao}: {len(recursos_regiao)} recursos coletados")
                
            except Exception as e:
                logger.warning(f"Erro ao coletar recursos da região {regiao}: {e}")
                continue
        
        # Coletar S3 (global)
        try:
            recursos_s3 = await self.repositorio_recursos.obter_recursos_s3()
            todos_recursos.extend(recursos_s3)
            logger.info(f"✓ S3 Global: {len(recursos_s3)} buckets coletados")
        except Exception as e:
            logger.warning(f"Erro ao coletar buckets S3: {e}")
        
        return todos_recursos
    
    async def _enriquecer_com_metricas(
        self, 
        recursos: List[RecursoAWS], 
        periodo_dias: int
    ) -> List[RecursoAWS]:
        """
        Enriquece recursos com métricas de performance.
        
        Args:
            recursos: Lista de recursos
            periodo_dias: Período para coleta de métricas
            
        Returns:
            Lista de recursos enriquecidos com métricas
        """
        fim = datetime.now()
        inicio = fim - timedelta(days=periodo_dias)
        
        recursos_enriquecidos = []
        
        for i, recurso in enumerate(recursos):
            if i % 10 == 0:
                logger.debug(f"Coletando métricas: {i+1}/{len(recursos)}")
            
            try:
                metricas_enriquecidas = await self._coletar_metricas_recurso(
                    recurso, inicio, fim
                )
                
                # Criar nova instância com métricas
                recurso_enriquecido = RecursoAWS(
                    id_recurso=recurso.id_recurso,
                    tipo_recurso=recurso.tipo_recurso,
                    regiao=recurso.regiao,
                    id_conta=recurso.id_conta,
                    tags=recurso.tags,
                    configuracao=recurso.configuracao,
                    metricas=metricas_enriquecidas,
                    criado_em=recurso.criado_em,
                    atualizado_em=datetime.now()
                )
                
                recursos_enriquecidos.append(recurso_enriquecido)
                
            except Exception as e:
                logger.warning(f"Erro ao coletar métricas para {recurso.id_recurso}: {e}")
                # Adicionar recurso sem métricas
                recursos_enriquecidos.append(recurso)
                continue
        
        return recursos_enriquecidos
    
    async def _coletar_metricas_recurso(
        self, 
        recurso: RecursoAWS, 
        inicio: datetime, 
        fim: datetime
    ) -> MetricasRecurso:
        """
        Coleta métricas específicas para um recurso.
        
        Args:
            recurso: Recurso AWS
            inicio: Data/hora de início
            fim: Data/hora de fim
            
        Returns:
            Métricas do recurso
        """
        metricas = MetricasRecurso()
        
        try:
            # CPU Utilization (disponível para a maioria dos recursos)
            dados_cpu = await self.repositorio_metricas.obter_utilizacao_cpu(
                recurso.tipo_recurso, recurso.id_recurso, inicio, fim
            )
            metricas.utilizacao_cpu = [
                PontoMetrica(
                    timestamp=datetime.fromisoformat(dp['timestamp'].replace('Z', '+00:00')),
                    valor=dp['valor']
                )
                for dp in dados_cpu
            ]
            
            # Memory Utilization (quando disponível)
            dados_memoria = await self.repositorio_metricas.obter_utilizacao_memoria(
                recurso.tipo_recurso, recurso.id_recurso, inicio, fim
            )
            metricas.utilizacao_memoria = [
                PontoMetrica(
                    timestamp=datetime.fromisoformat(dp['timestamp'].replace('Z', '+00:00')),
                    valor=dp['valor']
                )
                for dp in dados_memoria
            ]
            
            # Network Metrics
            dados_rede = await self.repositorio_metricas.obter_metricas_rede(
                recurso.tipo_recurso, recurso.id_recurso, inicio, fim
            )
            
            if 'entrada' in dados_rede:
                metricas.entrada_rede = [
                    PontoMetrica(
                        timestamp=datetime.fromisoformat(dp['timestamp'].replace('Z', '+00:00')),
                        valor=dp['valor']
                    )
                    for dp in dados_rede['entrada']
                ]
            
            if 'saida' in dados_rede:
                metricas.saida_rede = [
                    PontoMetrica(
                        timestamp=datetime.fromisoformat(dp['timestamp'].replace('Z', '+00:00')),
                        valor=dp['valor']
                    )
                    for dp in dados_rede['saida']
                ]
            
            # Disk Metrics
            dados_disco = await self.repositorio_metricas.obter_metricas_disco(
                recurso.tipo_recurso, recurso.id_recurso, inicio, fim
            )
            
            if 'leitura' in dados_disco:
                metricas.operacoes_leitura_disco = [
                    PontoMetrica(
                        timestamp=datetime.fromisoformat(dp['timestamp'].replace('Z', '+00:00')),
                        valor=dp['valor']
                    )
                    for dp in dados_disco['leitura']
                ]
            
            if 'escrita' in dados_disco:
                metricas.operacoes_escrita_disco = [
                    PontoMetrica(
                        timestamp=datetime.fromisoformat(dp['timestamp'].replace('Z', '+00:00')),
                        valor=dp['valor']
                    )
                    for dp in dados_disco['escrita']
                ]
            
            # Métricas específicas por tipo de recurso
            if hasattr(self.repositorio_metricas, 'obter_metricas_especificas_por_tipo'):
                metricas_especificas = await self.repositorio_metricas.obter_metricas_especificas_por_tipo(
                    recurso.tipo_recurso, recurso.id_recurso, inicio, fim
                )
                
                for nome_metrica, dados_metrica in metricas_especificas.items():
                    metricas.metricas_customizadas[nome_metrica] = [
                        PontoMetrica(
                            timestamp=datetime.fromisoformat(dp['timestamp'].replace('Z', '+00:00')),
                            valor=dp['valor']
                        )
                        for dp in dados_metrica
                    ]
            
        except Exception as e:
            logger.warning(f"Erro ao coletar métricas para {recurso.id_recurso}: {e}")
        
        return metricas
    
    def obter_estatisticas_execucao(self) -> Dict[str, Any]:
        """Obtém estatísticas da última execução."""
        return {
            'servico_analise': self.servico_analise.__class__.__name__,
            'repositorio_recursos': self.repositorio_recursos.__class__.__name__,
            'repositorio_metricas': self.repositorio_metricas.__class__.__name__
        }