"""
Implementação do Repositório de Recursos AWS.
Implementa as interfaces do domínio para acesso aos dados da AWS.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from ...domain.repositories.repositorio_recursos import IRepositorioRecursos, IRepositorioMetricas
from ...domain.entities.recurso import (
    RecursoAWS, TipoRecurso, DadosCusto, MetricasRecurso, 
    PontoMetrica
)
from .cliente_aws import ClienteAWSSingleton, retry_aws_call, medir_tempo_execucao, GerenciadorPaginacao

logger = logging.getLogger(__name__)


class RepositorioRecursosAWS(IRepositorioRecursos):
    """
    Implementação concreta do repositório de recursos AWS.
    
    Implementa a interface IRepositorioRecursos seguindo o padrão Repository.
    Utiliza o cliente AWS singleton para otimização de performance.
    """
    
    def __init__(self, regiao: str = 'us-east-1', id_conta: str = ''):
        """
        Inicializa o repositório.
        
        Args:
            regiao: Região AWS padrão
            id_conta: ID da conta AWS
        """
        self.regiao = regiao
        self.id_conta = id_conta
        self.cliente_aws = ClienteAWSSingleton(regiao)
        logger.info(f"Repositório AWS inicializado para região: {regiao}")
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_recursos_ec2(self, regiao: str) -> List[RecursoAWS]:
        """
        Obtém todas as instâncias EC2 de uma região.
        
        Implementa paginação completa e tratamento de erros.
        Complexidade: O(n) onde n é o número de instâncias.
        """
        logger.info(f"Coletando recursos EC2 da região {regiao}")
        recursos = []
        
        try:
            ec2_client = self.cliente_aws.obter_cliente('ec2', regiao)
            
            # Usar paginação para obter todas as instâncias
            parametros = {
                'Filters': [
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
                ]
            }
            
            reservations = await GerenciadorPaginacao.paginar_com_paginator(
                ec2_client, 'describe_instances', parametros
            )
            
            for reservation in reservations:
                if 'Instances' in reservation:
                    for instance in reservation['Instances']:
                        recurso = self._converter_instancia_ec2_para_recurso(instance, regiao)
                        recursos.append(recurso)
            
            logger.info(f"✓ {len(recursos)} instâncias EC2 coletadas da região {regiao}")
            return recursos
            
        except Exception as e:
            logger.error(f"Erro ao coletar recursos EC2 da região {regiao}: {e}")
            return []
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_recursos_rds(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todas as instâncias RDS de uma região."""
        logger.info(f"Coletando recursos RDS da região {regiao}")
        recursos = []
        
        try:
            rds_client = self.cliente_aws.obter_cliente('rds', regiao)
            
            # Paginação para RDS
            db_instances = await GerenciadorPaginacao.paginar_com_paginator(
                rds_client, 'describe_db_instances', {}
            )
            
            for db_instance in db_instances:
                recurso = self._converter_instancia_rds_para_recurso(db_instance, regiao)
                recursos.append(recurso)
            
            logger.info(f"✓ {len(recursos)} instâncias RDS coletadas da região {regiao}")
            return recursos
            
        except Exception as e:
            logger.error(f"Erro ao coletar recursos RDS da região {regiao}: {e}")
            return []
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_recursos_elb(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todos os Load Balancers de uma região."""
        logger.info(f"Coletando recursos ELB da região {regiao}")
        recursos = []
        
        try:
            elbv2_client = self.cliente_aws.obter_cliente('elbv2', regiao)
            
            # Paginação para ELB
            load_balancers = await GerenciadorPaginacao.paginar_com_paginator(
                elbv2_client, 'describe_load_balancers', {}
            )
            
            for lb in load_balancers:
                recurso = self._converter_load_balancer_para_recurso(lb, regiao)
                recursos.append(recurso)
            
            logger.info(f"✓ {len(recursos)} Load Balancers coletados da região {regiao}")
            return recursos
            
        except Exception as e:
            logger.error(f"Erro ao coletar recursos ELB da região {regiao}: {e}")
            return []
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_recursos_lambda(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todas as funções Lambda de uma região."""
        logger.info(f"Coletando recursos Lambda da região {regiao}")
        recursos = []
        
        try:
            lambda_client = self.cliente_aws.obter_cliente('lambda', regiao)
            
            # Paginação para Lambda
            functions = await GerenciadorPaginacao.paginar_com_paginator(
                lambda_client, 'list_functions', {}
            )
            
            for function in functions:
                recurso = self._converter_funcao_lambda_para_recurso(function, regiao)
                recursos.append(recurso)
            
            logger.info(f"✓ {len(recursos)} funções Lambda coletadas da região {regiao}")
            return recursos
            
        except Exception as e:
            logger.error(f"Erro ao coletar recursos Lambda da região {regiao}: {e}")
            return []
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_recursos_ebs(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todos os volumes EBS de uma região."""
        logger.info(f"Coletando recursos EBS da região {regiao}")
        recursos = []
        
        try:
            ec2_client = self.cliente_aws.obter_cliente('ec2', regiao)
            
            # Paginação para EBS
            volumes = await GerenciadorPaginacao.paginar_com_paginator(
                ec2_client, 'describe_volumes', {}
            )
            
            for volume in volumes:
                recurso = self._converter_volume_ebs_para_recurso(volume, regiao)
                recursos.append(recurso)
            
            logger.info(f"✓ {len(recursos)} volumes EBS coletados da região {regiao}")
            return recursos
            
        except Exception as e:
            logger.error(f"Erro ao coletar recursos EBS da região {regiao}: {e}")
            return []
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_recursos_s3(self) -> List[RecursoAWS]:
        """Obtém todos os buckets S3 (serviço global)."""
        logger.info("Coletando recursos S3 (global)")
        recursos = []
        
        try:
            s3_client = self.cliente_aws.obter_cliente('s3')
            
            response = s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            
            for bucket in buckets:
                recurso = self._converter_bucket_s3_para_recurso(bucket)
                recursos.append(recurso)
            
            logger.info(f"✓ {len(recursos)} buckets S3 coletados")
            return recursos
            
        except Exception as e:
            logger.error(f"Erro ao coletar recursos S3: {e}")
            return []
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_recursos_dynamodb(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todas as tabelas DynamoDB de uma região."""
        logger.info(f"Coletando recursos DynamoDB da região {regiao}")
        recursos = []
        
        try:
            dynamodb_client = self.cliente_aws.obter_cliente('dynamodb', regiao)
            
            # Paginação para DynamoDB
            table_names = await GerenciadorPaginacao.paginar_com_next_token(
                dynamodb_client, 'list_tables', {}, 'LastEvaluatedTableName', 'TableNames'
            )
            
            for table_name in table_names:
                # Obter detalhes da tabela
                response = dynamodb_client.describe_table(TableName=table_name)
                table = response['Table']
                
                recurso = self._converter_tabela_dynamodb_para_recurso(table, regiao)
                recursos.append(recurso)
            
            logger.info(f"✓ {len(recursos)} tabelas DynamoDB coletadas da região {regiao}")
            return recursos
            
        except Exception as e:
            logger.error(f"Erro ao coletar recursos DynamoDB da região {regiao}: {e}")
            return []
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_recursos_elasticache(self, regiao: str) -> List[RecursoAWS]:
        """Obtém todos os clusters ElastiCache de uma região."""
        logger.info(f"Coletando recursos ElastiCache da região {regiao}")
        recursos = []
        
        try:
            elasticache_client = self.cliente_aws.obter_cliente('elasticache', regiao)
            
            # Paginação para ElastiCache
            clusters = await GerenciadorPaginacao.paginar_com_paginator(
                elasticache_client, 'describe_cache_clusters', {}
            )
            
            for cluster in clusters:
                recurso = self._converter_cluster_elasticache_para_recurso(cluster, regiao)
                recursos.append(recurso)
            
            logger.info(f"✓ {len(recursos)} clusters ElastiCache coletados da região {regiao}")
            return recursos
            
        except Exception as e:
            logger.error(f"Erro ao coletar recursos ElastiCache da região {regiao}: {e}")
            return []
    
    @retry_aws_call(max_tentativas=3)
    @medir_tempo_execucao
    async def obter_dados_custo(self, dias: int) -> DadosCusto:
        """Obtém dados de custo para o número especificado de dias."""
        logger.info(f"Coletando dados de custo dos últimos {dias} dias")
        
        try:
            ce_client = self.cliente_aws.obter_cliente('ce')
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=dias)
            
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Processar dados de custo
            custo_por_servico = {}
            custos_diarios = []
            
            for result in response['ResultsByTime']:
                data = result['TimePeriod']['Start']
                custo_dia = 0.0
                
                for group in result['Groups']:
                    servico = group['Keys'][0]
                    custo = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if servico not in custo_por_servico:
                        custo_por_servico[servico] = Decimal('0')
                    custo_por_servico[servico] += Decimal(str(custo))
                    custo_dia += custo
                
                custos_diarios.append({
                    'data': data,
                    'custo_usd': custo_dia
                })
            
            custo_total = sum(custo_por_servico.values())
            
            dados_custo = DadosCusto(
                custo_total_usd=custo_total,
                periodo_dias=dias,
                custo_por_servico=custo_por_servico,
                custos_diarios=custos_diarios
            )
            
            logger.info(f"✓ Dados de custo coletados: ${custo_total:.2f} em {dias} dias")
            return dados_custo
            
        except Exception as e:
            logger.error(f"Erro ao coletar dados de custo: {e}")
            return DadosCusto(custo_total_usd=Decimal('0'), periodo_dias=dias)
    
    # Métodos privados para conversão de dados
    
    def _converter_instancia_ec2_para_recurso(self, instance: Dict[str, Any], regiao: str) -> RecursoAWS:
        """Converte instância EC2 para entidade RecursoAWS."""
        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
        
        configuracao = {
            'instance_type': instance['InstanceType'],
            'state': instance['State']['Name'],
            'launch_time': instance['LaunchTime'].isoformat(),
            'availability_zone': instance['Placement']['AvailabilityZone'],
            'vpc_id': instance.get('VpcId', ''),
            'subnet_id': instance.get('SubnetId', ''),
            'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])]
        }
        
        return RecursoAWS(
            id_recurso=instance['InstanceId'],
            tipo_recurso=TipoRecurso.EC2,
            regiao=regiao,
            id_conta=self.id_conta,
            tags=tags,
            configuracao=configuracao,
            criado_em=instance['LaunchTime']
        )
    
    def _converter_instancia_rds_para_recurso(self, db_instance: Dict[str, Any], regiao: str) -> RecursoAWS:
        """Converte instância RDS para entidade RecursoAWS."""
        configuracao = {
            'db_instance_class': db_instance['DBInstanceClass'],
            'engine': db_instance['Engine'],
            'engine_version': db_instance['EngineVersion'],
            'allocated_storage': db_instance['AllocatedStorage'],
            'storage_type': db_instance['StorageType'],
            'multi_az': db_instance['MultiAZ'],
            'availability_zone': db_instance['AvailabilityZone']
        }
        
        return RecursoAWS(
            id_recurso=db_instance['DBInstanceIdentifier'],
            tipo_recurso=TipoRecurso.RDS,
            regiao=regiao,
            id_conta=self.id_conta,
            configuracao=configuracao,
            criado_em=db_instance.get('InstanceCreateTime')
        )
    
    def _converter_load_balancer_para_recurso(self, lb: Dict[str, Any], regiao: str) -> RecursoAWS:
        """Converte Load Balancer para entidade RecursoAWS."""
        configuracao = {
            'type': lb['Type'],
            'scheme': lb['Scheme'],
            'availability_zones': [az['ZoneName'] for az in lb['AvailabilityZones']],
            'vpc_id': lb.get('VpcId', ''),
            'dns_name': lb['DNSName']
        }
        
        return RecursoAWS(
            id_recurso=lb['LoadBalancerName'],
            tipo_recurso=TipoRecurso.ELB,
            regiao=regiao,
            id_conta=self.id_conta,
            configuracao=configuracao,
            criado_em=lb.get('CreatedTime')
        )
    
    def _converter_funcao_lambda_para_recurso(self, function: Dict[str, Any], regiao: str) -> RecursoAWS:
        """Converte função Lambda para entidade RecursoAWS."""
        configuracao = {
            'runtime': function['Runtime'],
            'memory_size': function['MemorySize'],
            'timeout': function['Timeout'],
            'handler': function['Handler'],
            'code_size': function['CodeSize'],
            'last_modified': function['LastModified']
        }
        
        return RecursoAWS(
            id_recurso=function['FunctionName'],
            tipo_recurso=TipoRecurso.LAMBDA,
            regiao=regiao,
            id_conta=self.id_conta,
            configuracao=configuracao
        )
    
    def _converter_volume_ebs_para_recurso(self, volume: Dict[str, Any], regiao: str) -> RecursoAWS:
        """Converte volume EBS para entidade RecursoAWS."""
        tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
        
        configuracao = {
            'size_gb': volume['Size'],
            'volume_type': volume['VolumeType'],
            'iops': volume.get('Iops', 0),
            'state': volume['State'],
            'encrypted': volume.get('Encrypted', False),
            'availability_zone': volume['AvailabilityZone'],
            'attached_to': volume['Attachments'][0]['InstanceId'] if volume['Attachments'] else None
        }
        
        return RecursoAWS(
            id_recurso=volume['VolumeId'],
            tipo_recurso=TipoRecurso.EBS,
            regiao=regiao,
            id_conta=self.id_conta,
            tags=tags,
            configuracao=configuracao,
            criado_em=volume.get('CreateTime')
        )
    
    def _converter_bucket_s3_para_recurso(self, bucket: Dict[str, Any]) -> RecursoAWS:
        """Converte bucket S3 para entidade RecursoAWS."""
        configuracao = {
            'creation_date': bucket['CreationDate'].isoformat()
        }
        
        return RecursoAWS(
            id_recurso=bucket['Name'],
            tipo_recurso=TipoRecurso.S3,
            regiao='global',  # S3 é global
            id_conta=self.id_conta,
            configuracao=configuracao,
            criado_em=bucket['CreationDate']
        )
    
    def _converter_tabela_dynamodb_para_recurso(self, table: Dict[str, Any], regiao: str) -> RecursoAWS:
        """Converte tabela DynamoDB para entidade RecursoAWS."""
        configuracao = {
            'table_status': table['TableStatus'],
            'item_count': table.get('ItemCount', 0),
            'table_size_bytes': table.get('TableSizeBytes', 0),
            'billing_mode': table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
        }
        
        if 'ProvisionedThroughput' in table:
            configuracao.update({
                'read_capacity_units': table['ProvisionedThroughput'].get('ReadCapacityUnits', 0),
                'write_capacity_units': table['ProvisionedThroughput'].get('WriteCapacityUnits', 0)
            })
        
        return RecursoAWS(
            id_recurso=table['TableName'],
            tipo_recurso=TipoRecurso.DYNAMODB,
            regiao=regiao,
            id_conta=self.id_conta,
            configuracao=configuracao,
            criado_em=table.get('CreationDateTime')
        )
    
    def _converter_cluster_elasticache_para_recurso(self, cluster: Dict[str, Any], regiao: str) -> RecursoAWS:
        """Converte cluster ElastiCache para entidade RecursoAWS."""
        configuracao = {
            'cache_node_type': cluster['CacheNodeType'],
            'engine': cluster['Engine'],
            'engine_version': cluster['EngineVersion'],
            'num_cache_nodes': cluster['NumCacheNodes'],
            'cache_cluster_status': cluster['CacheClusterStatus'],
            'preferred_availability_zone': cluster.get('PreferredAvailabilityZone', '')
        }
        
        return RecursoAWS(
            id_recurso=cluster['CacheClusterId'],
            tipo_recurso=TipoRecurso.ELASTICACHE,
            regiao=regiao,
            id_conta=self.id_conta,
            configuracao=configuracao,
            criado_em=cluster.get('CacheClusterCreateTime')
        )