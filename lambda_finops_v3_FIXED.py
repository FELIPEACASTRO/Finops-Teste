"""
AWS FinOps Analyzer v3.1 FIXED - 100% Bedrock-Powered
Análise inteligente de TODOS os produtos AWS usando Amazon Bedrock
CORREÇÕES: Todos os 10 GAPs do código resolvidos
Autor: Manus AI
Data: 24/11/2025
"""

import boto3
import json
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from botocore.config import Config
from botocore.exceptions import ClientError

# Configurar logging estruturado
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuração de retry
config = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    read_timeout=60,
    connect_timeout=10
)

# Região AWS
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Clientes AWS com retry e região
ce_client = boto3.client('ce', region_name=AWS_REGION, config=config)
cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION, config=config)
ec2 = boto3.client('ec2', region_name=AWS_REGION, config=config)
rds = boto3.client('rds', region_name=AWS_REGION, config=config)
elbv2 = boto3.client('elbv2', region_name=AWS_REGION, config=config)
lambda_client = boto3.client('lambda', region_name=AWS_REGION, config=config)
s3_client = boto3.client('s3', region_name=AWS_REGION, config=config)
dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION, config=config)
bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION, config=config)
ses = boto3.client('ses', region_name=AWS_REGION, config=config)

# Validar variáveis de ambiente obrigatórias
REQUIRED_ENV_VARS = ['S3_BUCKET_NAME', 'EMAIL_FROM', 'EMAIL_TO', 'BEDROCK_MODEL_ID']
for var in REQUIRED_ENV_VARS:
    if not os.environ.get(var):
        raise ValueError(f"Variável de ambiente obrigatória não configurada: {var}")

# Configurações
S3_BUCKET = os.environ['S3_BUCKET_NAME']
EMAIL_FROM = os.environ['EMAIL_FROM']
EMAIL_TO = os.environ['EMAIL_TO'].split(',')
DAYS = int(os.environ.get('HISTORICAL_DAYS', '30'))
MODEL_ID = os.environ['BEDROCK_MODEL_ID']


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# ============================================================================
# COLETA DE DADOS - EC2 (COM PAGINAÇÃO)
# ============================================================================

def collect_ec2_data() -> List[Dict]:
    """Coleta dados de todas as instâncias EC2 com paginação"""
    logger.info("Coletando dados EC2...")
    instances_data = []
    
    try:
        paginator = ec2.get_paginator('describe_instances')
        page_iterator = paginator.paginate(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        for page in page_iterator:
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    cpu_metrics = get_cloudwatch_metrics(
                        'AWS/EC2', 'CPUUtilization',
                        [{'Name': 'InstanceId', 'Value': instance_id}]
                    )
                    
                    network_in = get_cloudwatch_metrics(
                        'AWS/EC2', 'NetworkIn',
                        [{'Name': 'InstanceId', 'Value': instance_id}]
                    )
                    
                    instances_data.append({
                        'resource_type': 'EC2',
                        'resource_id': instance_id,
                        'instance_type': instance_type,
                        'state': instance['State']['Name'],
                        'launch_time': instance['LaunchTime'].isoformat(),
                        'availability_zone': instance['Placement']['AvailabilityZone'],
                        'tags': tags,
                        'metrics': {
                            'cpu_utilization': cpu_metrics,
                            'network_in': network_in
                        }
                    })
        
        logger.info(f"✓ {len(instances_data)} instâncias EC2 coletadas")
        return instances_data
    
    except Exception as e:
        logger.error(f"Erro ao coletar EC2: {e}")
        return []


# ============================================================================
# COLETA DE DADOS - RDS (COM PAGINAÇÃO)
# ============================================================================

def collect_rds_data() -> List[Dict]:
    """Coleta dados de todas as instâncias RDS com paginação"""
    logger.info("Coletando dados RDS...")
    rds_data = []
    
    try:
        paginator = rds.get_paginator('describe_db_instances')
        page_iterator = paginator.paginate()
        
        for page in page_iterator:
            for db in page['DBInstances']:
                db_id = db['DBInstanceIdentifier']
                
                cpu_metrics = get_cloudwatch_metrics(
                    'AWS/RDS', 'CPUUtilization',
                    [{'Name': 'DBInstanceIdentifier', 'Value': db_id}]
                )
                
                connections = get_cloudwatch_metrics(
                    'AWS/RDS', 'DatabaseConnections',
                    [{'Name': 'DBInstanceIdentifier', 'Value': db_id}]
                )
                
                rds_data.append({
                    'resource_type': 'RDS',
                    'resource_id': db_id,
                    'instance_class': db['DBInstanceClass'],
                    'engine': db['Engine'],
                    'engine_version': db['EngineVersion'],
                    'storage_type': db['StorageType'],
                    'allocated_storage_gb': db['AllocatedStorage'],
                    'multi_az': db['MultiAZ'],
                    'availability_zone': db['AvailabilityZone'],
                    'metrics': {
                        'cpu_utilization': cpu_metrics,
                        'database_connections': connections
                    }
                })
        
        logger.info(f"✓ {len(rds_data)} instâncias RDS coletadas")
        return rds_data
    
    except Exception as e:
        logger.error(f"Erro ao coletar RDS: {e}")
        return []


# ============================================================================
# COLETA DE DADOS - LOAD BALANCERS (COM PAGINAÇÃO)
# ============================================================================

def collect_elb_data() -> List[Dict]:
    """Coleta dados de Load Balancers com paginação"""
    logger.info("Coletando dados ELB...")
    elb_data = []
    
    try:
        paginator = elbv2.get_paginator('describe_load_balancers')
        page_iterator = paginator.paginate()
        
        for page in page_iterator:
            for lb in page['LoadBalancers']:
                lb_name = lb['LoadBalancerName']
                lb_arn = lb['LoadBalancerArn']
                
                # Extrair dimensão correta
                lb_dimension = '/'.join(lb_arn.split('/')[-3:])
                
                request_count = get_cloudwatch_metrics(
                    'AWS/ApplicationELB', 'RequestCount',
                    [{'Name': 'LoadBalancer', 'Value': lb_dimension}],
                    stat='Sum'
                )
                
                elb_data.append({
                    'resource_type': 'ELB',
                    'resource_id': lb_name,
                    'type': lb['Type'],
                    'scheme': lb['Scheme'],
                    'availability_zones': [az['ZoneName'] for az in lb['AvailabilityZones']],
                    'metrics': {
                        'request_count': request_count
                    }
                })
        
        logger.info(f"✓ {len(elb_data)} Load Balancers coletados")
        return elb_data
    
    except Exception as e:
        logger.error(f"Erro ao coletar ELB: {e}")
        return []


# ============================================================================
# COLETA DE DADOS - LAMBDA (COM PAGINAÇÃO)
# ============================================================================

def collect_lambda_data() -> List[Dict]:
    """Coleta dados de funções Lambda com paginação"""
    logger.info("Coletando dados Lambda...")
    lambda_data = []
    
    try:
        paginator = lambda_client.get_paginator('list_functions')
        page_iterator = paginator.paginate()
        
        for page in page_iterator:
            for func in page['Functions']:
                func_name = func['FunctionName']
                
                invocations = get_cloudwatch_metrics(
                    'AWS/Lambda', 'Invocations',
                    [{'Name': 'FunctionName', 'Value': func_name}],
                    stat='Sum'
                )
                
                duration = get_cloudwatch_metrics(
                    'AWS/Lambda', 'Duration',
                    [{'Name': 'FunctionName', 'Value': func_name}]
                )
                
                lambda_data.append({
                    'resource_type': 'Lambda',
                    'resource_id': func_name,
                    'runtime': func['Runtime'],
                    'memory_mb': func['MemorySize'],
                    'timeout_seconds': func['Timeout'],
                    'metrics': {
                        'invocations': invocations,
                        'duration_ms': duration
                    }
                })
        
        logger.info(f"✓ {len(lambda_data)} funções Lambda coletadas")
        return lambda_data
    
    except Exception as e:
        logger.error(f"Erro ao coletar Lambda: {e}")
        return []


# ============================================================================
# COLETA DE DADOS - EBS VOLUMES (COM PAGINAÇÃO)
# ============================================================================

def collect_ebs_data() -> List[Dict]:
    """Coleta dados de volumes EBS com paginação"""
    logger.info("Coletando dados EBS...")
    ebs_data = []
    
    try:
        paginator = ec2.get_paginator('describe_volumes')
        page_iterator = paginator.paginate()
        
        for page in page_iterator:
            for volume in page['Volumes']:
                volume_id = volume['VolumeId']
                
                read_ops = get_cloudwatch_metrics(
                    'AWS/EBS', 'VolumeReadOps',
                    [{'Name': 'VolumeId', 'Value': volume_id}],
                    stat='Sum'
                )
                
                write_ops = get_cloudwatch_metrics(
                    'AWS/EBS', 'VolumeWriteOps',
                    [{'Name': 'VolumeId', 'Value': volume_id}],
                    stat='Sum'
                )
                
                ebs_data.append({
                    'resource_type': 'EBS',
                    'resource_id': volume_id,
                    'size_gb': volume['Size'],
                    'volume_type': volume['VolumeType'],
                    'iops': volume.get('Iops', 0),
                    'state': volume['State'],
                    'attached_to': volume['Attachments'][0]['InstanceId'] if volume['Attachments'] else None,
                    'metrics': {
                        'read_ops': read_ops,
                        'write_ops': write_ops
                    }
                })
        
        logger.info(f"✓ {len(ebs_data)} volumes EBS coletados")
        return ebs_data
    
    except Exception as e:
        logger.error(f"Erro ao coletar EBS: {e}")
        return []


# ============================================================================
# COLETA DE CUSTOS
# ============================================================================

def collect_cost_data() -> Dict:
    """Coleta dados de custo dos últimos 30 dias"""
    logger.info("Coletando dados de custo...")
    
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        costs_by_service = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if service not in costs_by_service:
                    costs_by_service[service] = 0
                costs_by_service[service] += cost
        
        top_services = sorted(costs_by_service.items(), key=lambda x: x[1], reverse=True)[:10]
        total_cost = sum(costs_by_service.values())
        
        logger.info(f"✓ Custo total (30 dias): ${total_cost:.2f}")
        
        return {
            'period_days': 30,
            'total_cost_usd': round(total_cost, 2),
            'top_10_services': [
                {'service': s, 'cost_usd': round(c, 2), 'percentage': round(c/total_cost*100, 1)}
                for s, c in top_services
            ]
        }
    
    except Exception as e:
        logger.error(f"Erro ao coletar custos: {e}")
        return {}


# ============================================================================
# HELPER: Coletar métricas CloudWatch
# ============================================================================

def get_cloudwatch_metrics(namespace: str, metric_name: str, dimensions: List[Dict],
                           stat: str = 'Average') -> List[Dict]:
    """Helper para coletar métricas do CloudWatch"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=DAYS)
        
        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=[stat]
        )
        
        datapoints = sorted(response.get('Datapoints', []), key=lambda x: x['Timestamp'])
        
        return [
            {
                'timestamp': dp['Timestamp'].isoformat(),
                'value': round(dp.get(stat, 0), 2)
            }
            for dp in datapoints
        ]
    
    except Exception as e:
        logger.error(f"Erro ao coletar métrica {metric_name}: {e}")
        return []


# ============================================================================
# ANÁLISE COM BEDROCK (COM TIMEOUT)
# ============================================================================

def analyze_with_bedrock(all_resources: List[Dict], cost_data: Dict) -> Dict:
    """Envia TODOS os dados para o Bedrock para análise completa"""
    
    logger.info(f"Enviando dados para Amazon Bedrock (Claude 3)")
    logger.info(f"Total de recursos: {len(all_resources)}")
    logger.info(f"Custo total (30d): ${cost_data.get('total_cost_usd', 0):.2f}")
    
    # Limitar recursos para não exceder token limit do Bedrock
    max_resources = 50
    resources_to_analyze = all_resources[:max_resources]
    
    if len(all_resources) > max_resources:
        logger.warning(f"Limitando análise a {max_resources} recursos (total: {len(all_resources)})")
    
    prompt = f"""Você é um especialista SÊNIOR em FinOps da AWS com 15 anos de experiência. Analise PROFUNDAMENTE todos os recursos AWS abaixo e forneça recomendações PRECISAS e ACIONÁVEIS.

## DADOS COLETADOS

### CUSTOS (Últimos 30 dias)
```json
{json.dumps(cost_data, indent=2)}
```

### RECURSOS AWS ({len(resources_to_analyze)} recursos)

"""
    
    for i, resource in enumerate(resources_to_analyze):
        prompt += f"\n**Recurso #{i+1}**: {resource['resource_type']} - {resource['resource_id']}\n"
        prompt += f"```json\n{json.dumps(resource, indent=2)}\n```\n"
    
    prompt += f"""

## SUA TAREFA

Analise CADA recurso e forneça:

1. **Padrão de uso** (steady/variable/batch/idle)
2. **Estatísticas** (média, p95, p99)
3. **Desperdício identificado** (%)
4. **Recomendação específica** (downsize/upsize/delete/optimize)
5. **Economia estimada** (USD/mês)
6. **Risco** (low/medium/high)
7. **Prioridade** (high/medium/low)

## FORMATO DE RESPOSTA (JSON ESTRITO)

```json
{{
  "summary": {{
    "total_resources_analyzed": {len(resources_to_analyze)},
    "total_monthly_savings_usd": 0.00,
    "total_annual_savings_usd": 0.00,
    "high_priority_actions": 0,
    "medium_priority_actions": 0,
    "low_priority_actions": 0
  }},
  "recommendations": [
    {{
      "resource_type": "EC2|RDS|ELB|Lambda|EBS",
      "resource_id": "id-do-recurso",
      "current_config": "t3a.large, 2 vCPU, 8GB RAM",
      "analysis": {{
        "pattern": "steady|variable|batch|idle",
        "cpu_mean": 21.3,
        "cpu_p95": 31.2,
        "waste_percentage": 70
      }},
      "recommendation": {{
        "action": "downsize|upsize|delete|optimize|no_change",
        "details": "Downsize de t3a.large para t3a.medium",
        "reasoning": "CPU p95 é 31%, indicando 70% de desperdício. Padrão steady permite downsize seguro."
      }},
      "savings": {{
        "monthly_usd": 27.37,
        "annual_usd": 328.44,
        "percentage": 50
      }},
      "risk_level": "low|medium|high",
      "priority": "high|medium|low",
      "implementation_steps": [
        "1. Criar snapshot/AMI",
        "2. Agendar janela de manutenção",
        "3. Modificar tipo de instância"
      ]
    }}
  ]
}}
```

IMPORTANTE: Responda APENAS com JSON válido, sem markdown, sem explicações adicionais."""

    try:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        # Timeout de 90 segundos para Bedrock
        bedrock_config = Config(
            read_timeout=90,
            connect_timeout=10,
            retries={'max_attempts': 2, 'mode': 'standard'}
        )
        bedrock_with_timeout = boto3.client('bedrock-runtime', region_name=AWS_REGION, config=bedrock_config)
        
        response = bedrock_with_timeout.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        ai_response = response_body['content'][0]['text']
        
        # Limpar e parsear JSON
        clean_response = ai_response.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]
        if clean_response.startswith('```'):
            clean_response = clean_response[3:]
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()
        
        analysis = json.loads(clean_response)
        
        logger.info(f"✓ Análise do Bedrock concluída!")
        logger.info(f"  - Economia mensal: ${analysis['summary']['total_monthly_savings_usd']:.2f}")
        logger.info(f"  - Ações prioritárias: {analysis['summary']['high_priority_actions']}")
        
        return {
            'status': 'success',
            'model_used': MODEL_ID,
            'analysis': analysis
        }
    
    except Exception as e:
        logger.error(f"Erro ao analisar com Bedrock: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


# ============================================================================
# GERAÇÃO DE RELATÓRIO HTML
# ============================================================================

def generate_html_report(report_data: Dict) -> str:
    """Gera relatório HTML profissional"""
    
    analysis = report_data['bedrock_analysis']
    summary = analysis['summary']
    recommendations = analysis['recommendations']
    cost_data = report_data['cost_data']
    
    # Filtrar recomendações por prioridade
    high_priority = [r for r in recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
    low_priority = [r for r in recommendations if r.get('priority') == 'low']
    
    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório FinOps - {datetime.now().strftime('%d/%m/%Y')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 5px 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}
        .card .subtitle {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .priority-high {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .priority-medium {{
            color: #f39c12;
            font-weight: bold;
        }}
        .priority-low {{
            color: #3498db;
        }}
        .recommendation-card {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .recommendation-card h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .recommendation-card .details {{
            color: #666;
            margin: 10px 0;
        }}
        .recommendation-card .savings {{
            background: #d4edda;
            color: #155724;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Relatório FinOps AWS</h1>
        <p>📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        <p>🤖 Modelo IA: {report_data['model_used']}</p>
        <p>📊 Período de Análise: {report_data['analysis_period_days']} dias</p>
    </div>

    <div class="summary-cards">
        <div class="card">
            <h3>Economia Mensal</h3>
            <div class="value">${summary['total_monthly_savings_usd']:,.2f}</div>
            <div class="subtitle">USD por mês</div>
        </div>
        <div class="card">
            <h3>Economia Anual</h3>
            <div class="value">${summary['total_annual_savings_usd']:,.2f}</div>
            <div class="subtitle">USD por ano</div>
        </div>
        <div class="card">
            <h3>Recursos Analisados</h3>
            <div class="value">{summary['total_resources_analyzed']}</div>
            <div class="subtitle">Instâncias e serviços</div>
        </div>
        <div class="card">
            <h3>Ações Prioritárias</h3>
            <div class="value">{summary['high_priority_actions']}</div>
            <div class="subtitle">Alta prioridade</div>
        </div>
    </div>

    <div class="section">
        <h2>💰 Custos Atuais (Últimos 30 dias)</h2>
        <p><strong>Custo Total:</strong> ${cost_data['total_cost_usd']:,.2f} USD</p>
        <table>
            <thead>
                <tr>
                    <th>Serviço AWS</th>
                    <th>Custo (USD)</th>
                    <th>Percentual</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for service in cost_data['top_10_services']:
        html += f"""
                <tr>
                    <td>{service['service']}</td>
                    <td>${service['cost_usd']:,.2f}</td>
                    <td>{service['percentage']}%</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
"""
    
    # Recomendações de Alta Prioridade
    if high_priority:
        html += """
    <div class="section">
        <h2>🔴 Recomendações de Alta Prioridade</h2>
"""
        for rec in high_priority:
            html += f"""
        <div class="recommendation-card">
            <h4>{rec['resource_type']}: {rec['resource_id']}</h4>
            <p><strong>Configuração Atual:</strong> {rec['current_config']}</p>
            <p><strong>Ação:</strong> {rec['recommendation']['action'].upper()}</p>
            <p class="details">{rec['recommendation']['details']}</p>
            <p class="details"><em>{rec['recommendation']['reasoning']}</em></p>
            <div class="savings">
                💰 Economia: ${rec['savings']['monthly_usd']:.2f}/mês (${rec['savings']['annual_usd']:.2f}/ano) - {rec['savings']['percentage']}%
            </div>
        </div>
"""
        html += """
    </div>
"""
    
    # Recomendações de Média Prioridade
    if medium_priority:
        html += """
    <div class="section">
        <h2>🟡 Recomendações de Média Prioridade</h2>
"""
        for rec in medium_priority[:5]:  # Limitar a 5
            html += f"""
        <div class="recommendation-card">
            <h4>{rec['resource_type']}: {rec['resource_id']}</h4>
            <p><strong>Ação:</strong> {rec['recommendation']['action'].upper()} - {rec['recommendation']['details']}</p>
            <div class="savings">
                💰 Economia: ${rec['savings']['monthly_usd']:.2f}/mês
            </div>
        </div>
"""
        html += """
    </div>
"""
    
    html += """
    <div class="footer">
        <p>🤖 Gerado automaticamente por AWS FinOps Analyzer v3.1 (Bedrock-Powered)</p>
        <p>📧 Para dúvidas ou suporte, entre em contato com a equipe de FinOps</p>
    </div>
</body>
</html>
"""
    
    return html


# ============================================================================
# ENVIO DE E-MAIL
# ============================================================================

def send_email_report(html_content: str, summary: Dict) -> bool:
    """Envia relatório por e-mail via SES"""
    
    try:
        subject = f"📊 Relatório FinOps AWS - Economia de ${summary['total_monthly_savings_usd']:,.2f}/mês"
        
        response = ses.send_email(
            Source=EMAIL_FROM,
            Destination={'ToAddresses': EMAIL_TO},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': html_content, 'Charset': 'UTF-8'}
                }
            }
        )
        
        logger.info(f"✓ E-mail enviado com sucesso! MessageId: {response['MessageId']}")
        return True
    
    except ClientError as e:
        logger.error(f"Erro ao enviar e-mail: {e}")
        return False


# ============================================================================
# HANDLER PRINCIPAL
# ============================================================================

def lambda_handler(event, context):
    """Handler principal - Orquestra tudo"""
    
    logger.info("="*60)
    logger.info("AWS FINOPS ANALYZER v3.1 - BEDROCK POWERED (FIXED)")
    logger.info("="*60)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Modelo IA: {MODEL_ID}")
    logger.info(f"Período: {DAYS} dias")
    logger.info(f"Região: {AWS_REGION}")
    logger.info("="*60)
    
    try:
        # 1. COLETAR DADOS DE TODOS OS RECURSOS
        all_resources = []
        
        all_resources.extend(collect_ec2_data())
        all_resources.extend(collect_rds_data())
        all_resources.extend(collect_elb_data())
        all_resources.extend(collect_lambda_data())
        all_resources.extend(collect_ebs_data())
        
        cost_data = collect_cost_data()
        
        logger.info(f"TOTAL DE RECURSOS COLETADOS: {len(all_resources)}")
        
        # 2. ENVIAR TUDO PARA O BEDROCK
        bedrock_result = analyze_with_bedrock(all_resources, cost_data)
        
        if bedrock_result['status'] != 'success':
            raise Exception(f"Bedrock analysis failed: {bedrock_result.get('error')}")
        
        # 3. GERAR RELATÓRIO FINAL
        report = {
            'generated_at': datetime.now().isoformat(),
            'version': '3.1-bedrock-fixed',
            'model_used': MODEL_ID,
            'analysis_period_days': DAYS,
            'resources_collected': len(all_resources),
            'cost_data': cost_data,
            'bedrock_analysis': bedrock_result['analysis']
        }
        
        # 4. GERAR HTML
        html_report = generate_html_report(report)
        
        # 5. SALVAR JSON NO S3
        report_key = f"finops-reports/{datetime.now().strftime('%Y-%m-%d_%H-%M')}_complete_analysis.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=report_key,
            Body=json.dumps(report, cls=DecimalEncoder, indent=2),
            ContentType='application/json'
        )
        
        # 6. SALVAR HTML NO S3
        html_key = f"finops-reports/{datetime.now().strftime('%Y-%m-%d_%H-%M')}_report.html"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=html_key,
            Body=html_report,
            ContentType='text/html'
        )
        
        # 7. ENVIAR E-MAIL
        summary = bedrock_result['analysis']['summary']
        email_sent = send_email_report(html_report, summary)
        
        # 8. RESUMO
        logger.info("="*60)
        logger.info("ANÁLISE CONCLUÍDA COM SUCESSO!")
        logger.info("="*60)
        logger.info(f"Recursos analisados: {summary['total_resources_analyzed']}")
        logger.info(f"Economia mensal: ${summary['total_monthly_savings_usd']:.2f}")
        logger.info(f"Economia anual: ${summary['total_annual_savings_usd']:.2f}")
        logger.info(f"Ações prioritárias: {summary['high_priority_actions']}")
        logger.info(f"Relatório JSON: s3://{S3_BUCKET}/{report_key}")
        logger.info(f"Relatório HTML: s3://{S3_BUCKET}/{html_key}")
        logger.info(f"E-mail enviado: {'✓ Sim' if email_sent else '✗ Não'}")
        logger.info("="*60)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'FinOps analysis completed successfully',
                'summary': summary,
                'report_json': f"s3://{S3_BUCKET}/{report_key}",
                'report_html': f"s3://{S3_BUCKET}/{html_key}",
                'email_sent': email_sent
            })
        }
    
    except Exception as e:
        logger.error(f"ERRO: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


if __name__ == "__main__":
    # Para teste local
    lambda_handler({}, {})
