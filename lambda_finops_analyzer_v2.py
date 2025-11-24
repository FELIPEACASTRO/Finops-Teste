"""
AWS FinOps Analyzer Lambda Function - Version 2.0
Análise completa de custos e recomendações de otimização
Inclui: EC2, RDS, EBS, Lambda, S3, Load Balancers, NAT Gateways, IPs Elásticos, RI/SP Coverage
"""

import boto3
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from collections import defaultdict

# Clientes AWS
ce_client = boto3.client('ce')
co_client = boto3.client('compute-optimizer')
support_client = boto3.client('support')
cloudwatch_client = boto3.client('cloudwatch')
ec2_client = boto3.client('ec2')
rds_client = boto3.client('rds')
elbv2_client = boto3.client('elbv2')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses')

# Variáveis de ambiente
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'finops-reports')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE_NAME', 'finops-recommendations')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'finops@example.com')
EMAIL_TO = os.environ.get('EMAIL_TO', 'team@example.com').split(',')
CPU_THRESHOLD = float(os.environ.get('CPU_THRESHOLD', '10'))
SNAPSHOT_AGE_DAYS = int(os.environ.get('SNAPSHOT_AGE_DAYS', '90'))


class DecimalEncoder(json.JSONEncoder):
    """Encoder para lidar com tipos Decimal do DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def get_cost_and_usage(days: int = 30) -> Dict[str, Any]:
    """Obtém dados de custo e uso dos últimos N dias"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost', 'UsageQuantity'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        return response
    except Exception as e:
        print(f"Erro ao obter dados de custo: {str(e)}")
        return {}


def get_cost_by_tags(days: int = 30) -> Dict[str, Any]:
    """Obtém custos agrupados por tags (centro de custo, projeto, etc.)"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'TAG', 'Key': 'CostCenter'},
                {'Type': 'TAG', 'Key': 'Project'},
                {'Type': 'TAG', 'Key': 'Environment'}
            ]
        )
        return response
    except Exception as e:
        print(f"Erro ao obter custos por tags: {str(e)}")
        return {}


def get_savings_plans_coverage(days: int = 30) -> Dict[str, Any]:
    """Obtém cobertura de Savings Plans"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce_client.get_savings_plans_coverage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY'
        )
        return response
    except Exception as e:
        print(f"Erro ao obter cobertura de Savings Plans: {str(e)}")
        return {}


def get_reservation_utilization(days: int = 30) -> Dict[str, Any]:
    """Obtém utilização de Reserved Instances"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce_client.get_reservation_utilization(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY'
        )
        return response
    except Exception as e:
        print(f"Erro ao obter utilização de RIs: {str(e)}")
        return {}


def get_cost_anomalies(days: int = 30) -> List[Dict]:
    """Obtém anomalias de custo detectadas"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        response = ce_client.get_anomalies(
            DateInterval={
                'StartDate': start_date.strftime('%Y-%m-%d'),
                'EndDate': end_date.strftime('%Y-%m-%d')
            }
        )
        return response.get('Anomalies', [])
    except Exception as e:
        print(f"Erro ao obter anomalias de custo: {str(e)}")
        return []


def get_underutilized_rds_instances() -> List[Dict]:
    """Identifica instâncias RDS subutilizadas"""
    underutilized = []
    
    try:
        instances = rds_client.describe_db_instances()
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        for db_instance in instances['DBInstances']:
            db_id = db_instance['DBInstanceIdentifier']
            db_class = db_instance['DBInstanceClass']
            
            # Obter métricas de CPU
            cpu_metrics = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            # Obter métricas de conexões
            conn_metrics = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='DatabaseConnections',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            if cpu_metrics['Datapoints']:
                avg_cpu = sum(dp['Average'] for dp in cpu_metrics['Datapoints']) / len(cpu_metrics['Datapoints'])
                avg_conn = sum(dp['Average'] for dp in conn_metrics['Datapoints']) / len(conn_metrics['Datapoints']) if conn_metrics['Datapoints'] else 0
                
                if avg_cpu < CPU_THRESHOLD and avg_conn < 5:
                    underutilized.append({
                        'db_instance_id': db_id,
                        'db_instance_class': db_class,
                        'avg_cpu': round(avg_cpu, 2),
                        'avg_connections': round(avg_conn, 2),
                        'recommendation': 'Consider downsizing or using Aurora Serverless'
                    })
    
    except Exception as e:
        print(f"Erro ao identificar RDS subutilizadas: {str(e)}")
    
    return underutilized


def get_old_ebs_snapshots() -> List[Dict]:
    """Identifica snapshots EBS antigos"""
    old_snapshots = []
    
    try:
        snapshots = ec2_client.describe_snapshots(OwnerIds=['self'])
        cutoff_date = datetime.now() - timedelta(days=SNAPSHOT_AGE_DAYS)
        
        for snapshot in snapshots['Snapshots']:
            snapshot_date = snapshot['StartTime'].replace(tzinfo=None)
            age_days = (datetime.now() - snapshot_date).days
            
            if age_days > SNAPSHOT_AGE_DAYS:
                # Estimar custo (aproximadamente $0.05 per GB-month)
                size_gb = snapshot['VolumeSize']
                monthly_cost = size_gb * 0.05
                
                old_snapshots.append({
                    'snapshot_id': snapshot['SnapshotId'],
                    'volume_id': snapshot.get('VolumeId', 'N/A'),
                    'size_gb': size_gb,
                    'age_days': age_days,
                    'estimated_monthly_cost': f"${monthly_cost:.2f}",
                    'recommendation': 'Consider deleting if no longer needed'
                })
    
    except Exception as e:
        print(f"Erro ao identificar snapshots antigos: {str(e)}")
    
    return old_snapshots


def get_unattached_elastic_ips() -> List[Dict]:
    """Identifica IPs elásticos não associados"""
    unattached_ips = []
    
    try:
        addresses = ec2_client.describe_addresses()
        
        for address in addresses['Addresses']:
            if 'AssociationId' not in address:
                # IP não associado custa ~$3.60/mês
                unattached_ips.append({
                    'allocation_id': address['AllocationId'],
                    'public_ip': address['PublicIp'],
                    'estimated_monthly_cost': '$3.60',
                    'recommendation': 'Release if not needed'
                })
    
    except Exception as e:
        print(f"Erro ao identificar IPs elásticos: {str(e)}")
    
    return unattached_ips


def get_idle_load_balancers() -> List[Dict]:
    """Identifica Load Balancers ociosos"""
    idle_lbs = []
    
    try:
        load_balancers = elbv2_client.describe_load_balancers()
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        for lb in load_balancers['LoadBalancers']:
            lb_arn = lb['LoadBalancerArn']
            lb_name = lb['LoadBalancerName']
            lb_type = lb['Type']
            
            # Obter métricas de requisições
            request_metrics = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB' if lb_type == 'application' else 'AWS/NetworkELB',
                MetricName='RequestCount' if lb_type == 'application' else 'ProcessedBytes',
                Dimensions=[{'Name': 'LoadBalancer', 'Value': lb_arn.split('/')[-3] + '/' + lb_arn.split('/')[-2] + '/' + lb_arn.split('/')[-1]}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Sum']
            )
            
            if request_metrics['Datapoints']:
                total_requests = sum(dp['Sum'] for dp in request_metrics['Datapoints'])
                
                if total_requests < 100:  # Menos de 100 requisições em 7 dias
                    estimated_cost = 16.20 if lb_type == 'application' else 22.68
                    idle_lbs.append({
                        'load_balancer_name': lb_name,
                        'load_balancer_type': lb_type,
                        'total_requests_7days': int(total_requests),
                        'estimated_monthly_cost': f"${estimated_cost:.2f}",
                        'recommendation': 'Consider deleting if not in use'
                    })
    
    except Exception as e:
        print(f"Erro ao identificar Load Balancers ociosos: {str(e)}")
    
    return idle_lbs


def get_nat_gateway_usage() -> List[Dict]:
    """Analisa uso de NAT Gateways"""
    nat_gateways = []
    
    try:
        nats = ec2_client.describe_nat_gateways(
            Filters=[{'Name': 'state', 'Values': ['available']}]
        )
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        for nat in nats['NatGateways']:
            nat_id = nat['NatGatewayId']
            
            # Obter métricas de bytes transferidos
            bytes_metrics = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/NATGateway',
                MetricName='BytesOutToDestination',
                Dimensions=[{'Name': 'NatGatewayId', 'Value': nat_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Sum']
            )
            
            if bytes_metrics['Datapoints']:
                total_gb = sum(dp['Sum'] for dp in bytes_metrics['Datapoints']) / (1024**3)
                base_cost = 32.40  # ~$0.045/hour
                data_cost = total_gb * 0.045 * 4  # Estimativa mensal
                total_cost = base_cost + data_cost
                
                nat_gateways.append({
                    'nat_gateway_id': nat_id,
                    'total_gb_7days': round(total_gb, 2),
                    'estimated_monthly_cost': f"${total_cost:.2f}",
                    'recommendation': 'Consider consolidating NAT Gateways or using NAT instances for dev/test'
                })
    
    except Exception as e:
        print(f"Erro ao analisar NAT Gateways: {str(e)}")
    
    return nat_gateways


def analyze_s3_storage_classes() -> List[Dict]:
    """Analisa classes de armazenamento S3"""
    s3_recommendations = []
    
    try:
        buckets = s3_client.list_buckets()
        
        for bucket in buckets['Buckets']:
            bucket_name = bucket['Name']
            
            try:
                # Verificar se tem Intelligent-Tiering configurado
                lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                has_intelligent_tiering = any(
                    rule.get('Transitions', [{}])[0].get('StorageClass') == 'INTELLIGENT_TIERING'
                    for rule in lifecycle.get('Rules', [])
                )
                
                if not has_intelligent_tiering:
                    s3_recommendations.append({
                        'bucket_name': bucket_name,
                        'current_config': 'No Intelligent-Tiering',
                        'recommendation': 'Enable S3 Intelligent-Tiering for automatic cost optimization',
                        'potential_savings': 'Up to 70% on infrequently accessed data'
                    })
            
            except s3_client.exceptions.NoSuchLifecycleConfiguration:
                s3_recommendations.append({
                    'bucket_name': bucket_name,
                    'current_config': 'No lifecycle policy',
                    'recommendation': 'Configure lifecycle policy with Intelligent-Tiering',
                    'potential_savings': 'Up to 70% on infrequently accessed data'
                })
            except Exception:
                pass  # Bucket pode não ter permissões
    
    except Exception as e:
        print(f"Erro ao analisar S3: {str(e)}")
    
    return s3_recommendations


def analyze_ri_sp_coverage(sp_coverage: Dict, ri_utilization: Dict) -> List[Dict]:
    """Analisa cobertura de RI e Savings Plans"""
    recommendations = []
    
    try:
        # Analisar Savings Plans
        if sp_coverage.get('SavingsPlansCoverages'):
            for coverage in sp_coverage['SavingsPlansCoverages']:
                coverage_pct = float(coverage.get('Coverage', {}).get('CoverageHours', {}).get('CoverageHoursPercentage', 0))
                
                if coverage_pct < 70:
                    on_demand_cost = float(coverage.get('Coverage', {}).get('CoverageHours', {}).get('OnDemandCost', 0))
                    potential_savings = on_demand_cost * 0.30  # Estimativa de 30% de economia
                    
                    recommendations.append({
                        'category': 'Savings Plans Coverage',
                        'current_coverage': f"{coverage_pct:.1f}%",
                        'on_demand_cost': f"${on_demand_cost:.2f}",
                        'potential_monthly_savings': f"${potential_savings:.2f}",
                        'recommendation': 'Increase Savings Plans coverage to reduce On-Demand costs',
                        'priority': 'High'
                    })
        
        # Analisar Reserved Instances
        if ri_utilization.get('UtilizationsByTime'):
            for util in ri_utilization['UtilizationsByTime']:
                util_pct = float(util.get('Total', {}).get('UtilizationPercentage', 0))
                
                if util_pct < 70:
                    recommendations.append({
                        'category': 'Reserved Instance Utilization',
                        'current_utilization': f"{util_pct:.1f}%",
                        'recommendation': 'Review and modify Reserved Instances to match actual usage',
                        'priority': 'Medium'
                    })
    
    except Exception as e:
        print(f"Erro ao analisar RI/SP: {str(e)}")
    
    return recommendations


# Continuar com as funções existentes...
