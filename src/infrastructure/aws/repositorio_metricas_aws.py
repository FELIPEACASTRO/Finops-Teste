"""
Implementação do Repositório de Métricas AWS CloudWatch.
Coleta métricas de performance dos recursos AWS.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ...domain.repositories.repositorio_recursos import IRepositorioMetricas
from ...domain.entities.recurso import TipoRecurso, PontoMetrica
from .cliente_aws import ClienteAWSSingleton, retry_aws_call, medir_tempo_execucao

logger = logging.getLogger(__name__)


class RepositorioMetricasAWS(IRepositorioMetricas):
    """
    Implementação concreta do repositório de métricas CloudWatch.
    
    Coleta métricas de performance dos recursos AWS usando CloudWatch.
    Implementa cache e otimizações para reduzir custos de API.
    """
    
    def __init__(self, regiao: str = 'us-east-1'):
        """
        Inicializa o repositório de métricas.
        
        Args:
            regiao: Região AWS padrão
        """
        self.regiao = regiao
        self.cliente_aws = ClienteAWSSingleton(regiao)
        self._cache_metricas = {}  # Cache simples para evitar chamadas desnecessárias
        logger.info(f"Repositório de métricas inicializado para região: {regiao}")
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_utilizacao_cpu(
        self, 
        tipo_recurso: TipoRecurso, 
        id_recurso: str, 
        inicio: datetime, 
        fim: datetime
    ) -> List[Dict[str, Any]]:
        """
        Obtém métricas de utilização de CPU.
        
        Args:
            tipo_recurso: Tipo do recurso AWS
            id_recurso: ID do recurso
            inicio: Data/hora de início
            fim: Data/hora de fim
            
        Returns:
            Lista de pontos de métrica de CPU
        """
        namespace, dimensoes = self._obter_namespace_e_dimensoes(tipo_recurso, id_recurso)
        
        return await self._obter_metrica_cloudwatch(
            namespace=namespace,
            nome_metrica='CPUUtilization',
            dimensoes=dimensoes,
            inicio=inicio,
            fim=fim,
            estatistica='Average'
        )
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_utilizacao_memoria(
        self, 
        tipo_recurso: TipoRecurso, 
        id_recurso: str, 
        inicio: datetime, 
        fim: datetime
    ) -> List[Dict[str, Any]]:
        """Obtém métricas de utilização de memória."""
        namespace, dimensoes = self._obter_namespace_e_dimensoes(tipo_recurso, id_recurso)
        
        # Memória não está disponível por padrão para todos os recursos
        if tipo_recurso == TipoRecurso.EC2:
            # Para EC2, memória requer CloudWatch Agent
            return await self._obter_metrica_cloudwatch(
                namespace='CWAgent',
                nome_metrica='mem_used_percent',
                dimensoes=dimensoes,
                inicio=inicio,
                fim=fim,
                estatistica='Average'
            )
        elif tipo_recurso == TipoRecurso.RDS:
            # RDS tem métricas de memória disponíveis
            return await self._obter_metrica_cloudwatch(
                namespace=namespace,
                nome_metrica='FreeableMemory',
                dimensoes=dimensoes,
                inicio=inicio,
                fim=fim,
                estatistica='Average'
            )
        else:
            logger.warning(f"Métricas de memória não disponíveis para {tipo_recurso}")
            return []
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_metricas_rede(
        self, 
        tipo_recurso: TipoRecurso, 
        id_recurso: str, 
        inicio: datetime, 
        fim: datetime
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Obtém métricas de entrada/saída de rede."""
        namespace, dimensoes = self._obter_namespace_e_dimensoes(tipo_recurso, id_recurso)
        
        metricas_rede = {}
        
        # Network In
        metricas_rede['entrada'] = await self._obter_metrica_cloudwatch(
            namespace=namespace,
            nome_metrica='NetworkIn',
            dimensoes=dimensoes,
            inicio=inicio,
            fim=fim,
            estatistica='Sum'
        )
        
        # Network Out
        metricas_rede['saida'] = await self._obter_metrica_cloudwatch(
            namespace=namespace,
            nome_metrica='NetworkOut',
            dimensoes=dimensoes,
            inicio=inicio,
            fim=fim,
            estatistica='Sum'
        )
        
        return metricas_rede
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_metricas_disco(
        self, 
        tipo_recurso: TipoRecurso, 
        id_recurso: str, 
        inicio: datetime, 
        fim: datetime
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Obtém métricas de leitura/escrita de disco."""
        namespace, dimensoes = self._obter_namespace_e_dimensoes(tipo_recurso, id_recurso)
        
        metricas_disco = {}
        
        if tipo_recurso == TipoRecurso.EC2:
            # EC2 - Disk Read/Write Ops
            metricas_disco['leitura'] = await self._obter_metrica_cloudwatch(
                namespace=namespace,
                nome_metrica='DiskReadOps',
                dimensoes=dimensoes,
                inicio=inicio,
                fim=fim,
                estatistica='Sum'
            )
            
            metricas_disco['escrita'] = await self._obter_metrica_cloudwatch(
                namespace=namespace,
                nome_metrica='DiskWriteOps',
                dimensoes=dimensoes,
                inicio=inicio,
                fim=fim,
                estatistica='Sum'
            )
            
        elif tipo_recurso == TipoRecurso.EBS:
            # EBS - Volume Read/Write Ops
            metricas_disco['leitura'] = await self._obter_metrica_cloudwatch(
                namespace='AWS/EBS',
                nome_metrica='VolumeReadOps',
                dimensoes=[{'Name': 'VolumeId', 'Value': id_recurso}],
                inicio=inicio,
                fim=fim,
                estatistica='Sum'
            )
            
            metricas_disco['escrita'] = await self._obter_metrica_cloudwatch(
                namespace='AWS/EBS',
                nome_metrica='VolumeWriteOps',
                dimensoes=[{'Name': 'VolumeId', 'Value': id_recurso}],
                inicio=inicio,
                fim=fim,
                estatistica='Sum'
            )
            
        elif tipo_recurso == TipoRecurso.RDS:
            # RDS - Read/Write IOPS
            metricas_disco['leitura'] = await self._obter_metrica_cloudwatch(
                namespace=namespace,
                nome_metrica='ReadIOPS',
                dimensoes=dimensoes,
                inicio=inicio,
                fim=fim,
                estatistica='Average'
            )
            
            metricas_disco['escrita'] = await self._obter_metrica_cloudwatch(
                namespace=namespace,
                nome_metrica='WriteIOPS',
                dimensoes=dimensoes,
                inicio=inicio,
                fim=fim,
                estatistica='Average'
            )
        
        return metricas_disco
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_metricas_customizadas(
        self, 
        namespace: str,
        nome_metrica: str,
        dimensoes: List[Dict[str, str]], 
        inicio: datetime, 
        fim: datetime
    ) -> List[Dict[str, Any]]:
        """Obtém métricas customizadas do CloudWatch."""
        return await self._obter_metrica_cloudwatch(
            namespace=namespace,
            nome_metrica=nome_metrica,
            dimensoes=dimensoes,
            inicio=inicio,
            fim=fim,
            estatistica='Average'
        )
    
    async def obter_metricas_especificas_por_tipo(
        self,
        tipo_recurso: TipoRecurso,
        id_recurso: str,
        inicio: datetime,
        fim: datetime
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Obtém métricas específicas por tipo de recurso.
        
        Cada tipo de recurso tem métricas específicas importantes.
        """
        metricas_especificas = {}
        namespace, dimensoes = self._obter_namespace_e_dimensoes(tipo_recurso, id_recurso)
        
        try:
            if tipo_recurso == TipoRecurso.RDS:
                # Conexões de banco de dados
                metricas_especificas['database_connections'] = await self._obter_metrica_cloudwatch(
                    namespace=namespace,
                    nome_metrica='DatabaseConnections',
                    dimensoes=dimensoes,
                    inicio=inicio,
                    fim=fim,
                    estatistica='Average'
                )
                
            elif tipo_recurso == TipoRecurso.ELB:
                # Request Count para Load Balancers
                # Precisa ajustar dimensões para ALB
                if 'LoadBalancer' in dimensoes[0].get('Name', ''):
                    metricas_especificas['request_count'] = await self._obter_metrica_cloudwatch(
                        namespace='AWS/ApplicationELB',
                        nome_metrica='RequestCount',
                        dimensoes=dimensoes,
                        inicio=inicio,
                        fim=fim,
                        estatistica='Sum'
                    )
                    
            elif tipo_recurso == TipoRecurso.LAMBDA:
                # Invocations e Duration para Lambda
                metricas_especificas['invocations'] = await self._obter_metrica_cloudwatch(
                    namespace=namespace,
                    nome_metrica='Invocations',
                    dimensoes=dimensoes,
                    inicio=inicio,
                    fim=fim,
                    estatistica='Sum'
                )
                
                metricas_especificas['duration'] = await self._obter_metrica_cloudwatch(
                    namespace=namespace,
                    nome_metrica='Duration',
                    dimensoes=dimensoes,
                    inicio=inicio,
                    fim=fim,
                    estatistica='Average'
                )
                
                metricas_especificas['errors'] = await self._obter_metrica_cloudwatch(
                    namespace=namespace,
                    nome_metrica='Errors',
                    dimensoes=dimensoes,
                    inicio=inicio,
                    fim=fim,
                    estatistica='Sum'
                )
                
            elif tipo_recurso == TipoRecurso.DYNAMODB:
                # Consumed Read/Write Capacity Units
                metricas_especificas['consumed_read_capacity'] = await self._obter_metrica_cloudwatch(
                    namespace=namespace,
                    nome_metrica='ConsumedReadCapacityUnits',
                    dimensoes=dimensoes,
                    inicio=inicio,
                    fim=fim,
                    estatistica='Sum'
                )
                
                metricas_especificas['consumed_write_capacity'] = await self._obter_metrica_cloudwatch(
                    namespace=namespace,
                    nome_metrica='ConsumedWriteCapacityUnits',
                    dimensoes=dimensoes,
                    inicio=inicio,
                    fim=fim,
                    estatistica='Sum'
                )
                
        except Exception as e:
            logger.warning(f"Erro ao obter métricas específicas para {tipo_recurso}: {e}")
        
        return metricas_especificas
    
    async def _obter_metrica_cloudwatch(
        self,
        namespace: str,
        nome_metrica: str,
        dimensoes: List[Dict[str, str]],
        inicio: datetime,
        fim: datetime,
        estatistica: str = 'Average',
        periodo: int = 3600
    ) -> List[Dict[str, Any]]:
        """
        Método privado para obter métricas do CloudWatch.
        
        Args:
            namespace: Namespace da métrica
            nome_metrica: Nome da métrica
            dimensoes: Dimensões da métrica
            inicio: Data/hora de início
            fim: Data/hora de fim
            estatistica: Tipo de estatística
            periodo: Período em segundos
            
        Returns:
            Lista de pontos de métrica
        """
        # Verificar cache
        chave_cache = f"{namespace}_{nome_metrica}_{hash(str(dimensoes))}_{inicio}_{fim}"
        if chave_cache in self._cache_metricas:
            logger.debug(f"Usando cache para métrica {nome_metrica}")
            return self._cache_metricas[chave_cache]
        
        try:
            cloudwatch_client = self.cliente_aws.obter_cliente('cloudwatch', self.regiao)
            
            response = cloudwatch_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=nome_metrica,
                Dimensions=dimensoes,
                StartTime=inicio,
                EndTime=fim,
                Period=periodo,
                Statistics=[estatistica]
            )
            
            # Processar datapoints
            datapoints = response.get('Datapoints', [])
            datapoints_ordenados = sorted(datapoints, key=lambda x: x['Timestamp'])
            
            resultado = [
                {
                    'timestamp': dp['Timestamp'].isoformat(),
                    'valor': round(dp.get(estatistica, 0), 2)
                }
                for dp in datapoints_ordenados
            ]
            
            # Armazenar no cache
            self._cache_metricas[chave_cache] = resultado
            
            logger.debug(f"Coletados {len(resultado)} pontos para métrica {nome_metrica}")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao obter métrica {nome_metrica}: {e}")
            return []
    
    def _obter_namespace_e_dimensoes(
        self, 
        tipo_recurso: TipoRecurso, 
        id_recurso: str
    ) -> tuple[str, List[Dict[str, str]]]:
        """
        Obtém namespace e dimensões corretas para cada tipo de recurso.
        
        Args:
            tipo_recurso: Tipo do recurso
            id_recurso: ID do recurso
            
        Returns:
            Tupla com namespace e lista de dimensões
        """
        if tipo_recurso == TipoRecurso.EC2:
            return 'AWS/EC2', [{'Name': 'InstanceId', 'Value': id_recurso}]
            
        elif tipo_recurso == TipoRecurso.RDS:
            return 'AWS/RDS', [{'Name': 'DBInstanceIdentifier', 'Value': id_recurso}]
            
        elif tipo_recurso == TipoRecurso.ELB:
            # Para ALB, a dimensão é diferente
            return 'AWS/ApplicationELB', [{'Name': 'LoadBalancer', 'Value': id_recurso}]
            
        elif tipo_recurso == TipoRecurso.LAMBDA:
            return 'AWS/Lambda', [{'Name': 'FunctionName', 'Value': id_recurso}]
            
        elif tipo_recurso == TipoRecurso.EBS:
            return 'AWS/EBS', [{'Name': 'VolumeId', 'Value': id_recurso}]
            
        elif tipo_recurso == TipoRecurso.DYNAMODB:
            return 'AWS/DynamoDB', [{'Name': 'TableName', 'Value': id_recurso}]
            
        elif tipo_recurso == TipoRecurso.ELASTICACHE:
            return 'AWS/ElastiCache', [{'Name': 'CacheClusterId', 'Value': id_recurso}]
            
        elif tipo_recurso == TipoRecurso.S3:
            return 'AWS/S3', [{'Name': 'BucketName', 'Value': id_recurso}]
            
        else:
            logger.warning(f"Namespace não definido para tipo de recurso: {tipo_recurso}")
            return 'AWS/Unknown', [{'Name': 'ResourceId', 'Value': id_recurso}]
    
    def limpar_cache(self):
        """Limpa o cache de métricas."""
        self._cache_metricas.clear()
        logger.info("Cache de métricas limpo")
    
    def obter_estatisticas_cache(self) -> Dict[str, int]:
        """Obtém estatísticas do cache."""
        return {
            'total_entradas': len(self._cache_metricas),
            'tamanho_aproximado_mb': len(str(self._cache_metricas)) / (1024 * 1024)
        }