"""
AWS FinOps Analyzer Lambda Function
Analisa custos e gera recomendações de otimização diariamente
"""

import boto3
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

# Clientes AWS
ce_client = boto3.client('ce')  # Cost Explorer
co_client = boto3.client('compute-optimizer')  # Compute Optimizer
support_client = boto3.client('support')  # Trusted Advisor
cloudwatch_client = boto3.client('cloudwatch')
ec2_client = boto3.client('ec2')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses')

# Variáveis de ambiente
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'finops-reports')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE_NAME', 'finops-recommendations')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'finops@example.com')
EMAIL_TO = os.environ.get('EMAIL_TO', 'team@example.com').split(',')


class DecimalEncoder(json.JSONEncoder):
    """Encoder para lidar com tipos Decimal do DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def get_cost_and_usage(days: int = 30) -> Dict[str, Any]:
    """
    Obtém dados de custo e uso dos últimos N dias
    """
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
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        return response
    except Exception as e:
        print(f"Erro ao obter dados de custo: {str(e)}")
        return {}


def get_cost_forecast(days: int = 30) -> Dict[str, Any]:
    """
    Obtém previsão de custos para os próximos N dias
    """
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=days)
    
    try:
        response = ce_client.get_cost_forecast(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Metric='UNBLENDED_COST',
            Granularity='MONTHLY'
        )
        
        return response
    except Exception as e:
        print(f"Erro ao obter previsão de custo: {str(e)}")
        return {}


def get_compute_optimizer_recommendations() -> Dict[str, List]:
    """
    Obtém recomendações do Compute Optimizer para EC2, EBS, Lambda, ECS
    """
    recommendations = {
        'ec2': [],
        'ebs': [],
        'lambda': [],
        'ecs': []
    }
    
    try:
        # Recomendações de EC2
        ec2_response = co_client.get_ec2_instance_recommendations()
        recommendations['ec2'] = ec2_response.get('instanceRecommendations', [])
        
        # Recomendações de EBS
        ebs_response = co_client.get_ebs_volume_recommendations()
        recommendations['ebs'] = ebs_response.get('volumeRecommendations', [])
        
        # Recomendações de Lambda
        lambda_response = co_client.get_lambda_function_recommendations()
        recommendations['lambda'] = lambda_response.get('lambdaFunctionRecommendations', [])
        
        # Recomendações de ECS
        ecs_response = co_client.get_ecs_service_recommendations()
        recommendations['ecs'] = ecs_response.get('ecsServiceRecommendations', [])
        
    except Exception as e:
        print(f"Erro ao obter recomendações do Compute Optimizer: {str(e)}")
    
    return recommendations


def get_trusted_advisor_checks() -> List[Dict]:
    """
    Obtém verificações de otimização de custos do Trusted Advisor
    """
    cost_optimization_checks = []
    
    try:
        # Listar verificações disponíveis
        checks_response = support_client.describe_trusted_advisor_checks(
            language='en'
        )
        
        # Filtrar apenas verificações de otimização de custos
        for check in checks_response.get('checks', []):
            if check['category'] == 'cost_optimizing':
                check_id = check['id']
                
                # Obter resultados da verificação
                result_response = support_client.describe_trusted_advisor_check_result(
                    checkId=check_id,
                    language='en'
                )
                
                cost_optimization_checks.append({
                    'name': check['name'],
                    'description': check['description'],
                    'result': result_response['result']
                })
        
    except Exception as e:
        print(f"Erro ao obter verificações do Trusted Advisor: {str(e)}")
    
    return cost_optimization_checks


def get_underutilized_ec2_instances() -> List[Dict]:
    """
    Identifica instâncias EC2 subutilizadas com base em métricas do CloudWatch
    """
    underutilized = []
    
    try:
        # Obter todas as instâncias EC2 em execução
        instances_response = ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        for reservation in instances_response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                
                # Obter métricas de CPU
                cpu_metrics = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,  # 1 dia
                    Statistics=['Average']
                )
                
                if cpu_metrics['Datapoints']:
                    avg_cpu = sum(dp['Average'] for dp in cpu_metrics['Datapoints']) / len(cpu_metrics['Datapoints'])
                    
                    # Se CPU média < 10%, considerar subutilizada
                    if avg_cpu < 10:
                        underutilized.append({
                            'instance_id': instance_id,
                            'instance_type': instance_type,
                            'avg_cpu': round(avg_cpu, 2),
                            'recommendation': 'Consider downsizing or stopping this instance'
                        })
        
    except Exception as e:
        print(f"Erro ao identificar instâncias subutilizadas: {str(e)}")
    
    return underutilized


def analyze_costs_by_service(cost_data: Dict) -> List[Dict]:
    """
    Analisa custos por serviço e identifica os maiores gastadores
    """
    service_costs = {}
    
    for result in cost_data.get('ResultsByTime', []):
        for group in result.get('Groups', []):
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            
            if service in service_costs:
                service_costs[service] += cost
            else:
                service_costs[service] = cost
    
    # Ordenar por custo (maior para menor)
    sorted_services = sorted(
        [{'service': k, 'cost': v} for k, v in service_costs.items()],
        key=lambda x: x['cost'],
        reverse=True
    )
    
    return sorted_services


def generate_finops_recommendations(
    cost_data: Dict,
    compute_recommendations: Dict,
    trusted_advisor_checks: List,
    underutilized_instances: List
) -> List[Dict]:
    """
    Gera recomendações de FinOps consolidadas
    """
    recommendations = []
    
    # 1. Recomendações de EC2
    for ec2_rec in compute_recommendations.get('ec2', []):
        if ec2_rec.get('finding') in ['Underprovisioned', 'Overprovisioned']:
            current_type = ec2_rec.get('currentInstanceType', 'Unknown')
            recommended_type = ec2_rec.get('recommendationOptions', [{}])[0].get('instanceType', 'Unknown')
            estimated_savings = ec2_rec.get('recommendationOptions', [{}])[0].get('estimatedMonthlySavings', {}).get('value', 0)
            
            recommendations.append({
                'category': 'EC2 Right-Sizing',
                'resource': ec2_rec.get('instanceArn', 'Unknown'),
                'current': current_type,
                'recommended': recommended_type,
                'estimated_monthly_savings': f"${estimated_savings:.2f}",
                'priority': 'High' if estimated_savings > 50 else 'Medium'
            })
    
    # 2. Recomendações de EBS
    for ebs_rec in compute_recommendations.get('ebs', []):
        if ebs_rec.get('finding') == 'Optimized':
            continue
        
        recommendations.append({
            'category': 'EBS Optimization',
            'resource': ebs_rec.get('volumeArn', 'Unknown'),
            'current': ebs_rec.get('currentConfiguration', {}).get('volumeType', 'Unknown'),
            'recommended': ebs_rec.get('volumeRecommendationOptions', [{}])[0].get('configuration', {}).get('volumeType', 'Unknown'),
            'estimated_monthly_savings': f"${ebs_rec.get('volumeRecommendationOptions', [{}])[0].get('savingsOpportunity', {}).get('estimatedMonthlySavings', {}).get('value', 0):.2f}",
            'priority': 'Medium'
        })
    
    # 3. Instâncias subutilizadas
    for instance in underutilized_instances:
        recommendations.append({
            'category': 'EC2 Underutilized',
            'resource': instance['instance_id'],
            'current': instance['instance_type'],
            'avg_cpu': f"{instance['avg_cpu']}%",
            'recommended': instance['recommendation'],
            'priority': 'High'
        })
    
    # 4. Recomendações do Trusted Advisor
    for check in trusted_advisor_checks:
        if check['result'].get('flaggedResources'):
            recommendations.append({
                'category': 'Trusted Advisor',
                'check_name': check['name'],
                'description': check['description'],
                'flagged_resources': len(check['result']['flaggedResources']),
                'priority': 'Medium'
            })
    
    return recommendations


def format_html_report(
    cost_summary: List[Dict],
    forecast: Dict,
    recommendations: List[Dict]
) -> str:
    """
    Formata o relatório em HTML
    """
    total_cost = sum(item['cost'] for item in cost_summary)
    forecast_cost = float(forecast.get('Total', {}).get('Amount', 0))
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #FF9900; }}
            h2 {{ color: #232F3E; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #232F3E; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .high {{ color: red; font-weight: bold; }}
            .medium {{ color: orange; }}
            .summary {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>📊 Relatório Diário de FinOps - AWS</h1>
        <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>💰 Resumo de Custos</h2>
            <p><strong>Custo Total (últimos 30 dias):</strong> ${total_cost:.2f}</p>
            <p><strong>Previsão de Custo (próximos 30 dias):</strong> ${forecast_cost:.2f}</p>
        </div>
        
        <h2>🔝 Top 10 Serviços por Custo</h2>
        <table>
            <tr>
                <th>Serviço</th>
                <th>Custo (USD)</th>
                <th>% do Total</th>
            </tr>
    """
    
    for i, service in enumerate(cost_summary[:10]):
        percentage = (service['cost'] / total_cost * 100) if total_cost > 0 else 0
        html += f"""
            <tr>
                <td>{service['service']}</td>
                <td>${service['cost']:.2f}</td>
                <td>{percentage:.2f}%</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h2>💡 Recomendações de Otimização</h2>
        <table>
            <tr>
                <th>Categoria</th>
                <th>Recurso</th>
                <th>Recomendação</th>
                <th>Economia Estimada</th>
                <th>Prioridade</th>
            </tr>
    """
    
    for rec in recommendations:
        priority_class = 'high' if rec.get('priority') == 'High' else 'medium'
        html += f"""
            <tr>
                <td>{rec.get('category', 'N/A')}</td>
                <td>{rec.get('resource', 'N/A')}</td>
                <td>{rec.get('recommended', rec.get('description', 'N/A'))}</td>
                <td>{rec.get('estimated_monthly_savings', 'N/A')}</td>
                <td class="{priority_class}">{rec.get('priority', 'N/A')}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <hr>
        <p><em>Este relatório foi gerado automaticamente pelo Sistema de FinOps AWS.</em></p>
    </body>
    </html>
    """
    
    return html


def save_report_to_s3(report_html: str, report_data: Dict) -> str:
    """
    Salva o relatório no S3
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Salvar HTML
    html_key = f"reports/{timestamp}_report.html"
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=html_key,
        Body=report_html,
        ContentType='text/html'
    )
    
    # Salvar JSON
    json_key = f"reports/{timestamp}_data.json"
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=json_key,
        Body=json.dumps(report_data, cls=DecimalEncoder),
        ContentType='application/json'
    )
    
    return html_key


def save_recommendations_to_dynamodb(recommendations: List[Dict]):
    """
    Salva recomendações no DynamoDB para tracking
    """
    table = dynamodb.Table(DYNAMODB_TABLE)
    timestamp = datetime.now().isoformat()
    
    for rec in recommendations:
        try:
            table.put_item(
                Item={
                    'recommendation_id': f"{rec.get('resource', 'unknown')}_{timestamp}",
                    'timestamp': timestamp,
                    'category': rec.get('category', 'Unknown'),
                    'resource': rec.get('resource', 'Unknown'),
                    'recommendation': rec.get('recommended', rec.get('description', 'Unknown')),
                    'estimated_savings': rec.get('estimated_monthly_savings', 'N/A'),
                    'priority': rec.get('priority', 'Medium'),
                    'status': 'pending'
                }
            )
        except Exception as e:
            print(f"Erro ao salvar recomendação no DynamoDB: {str(e)}")


def send_email_report(html_content: str):
    """
    Envia o relatório por e-mail via SES
    """
    try:
        response = ses_client.send_email(
            Source=EMAIL_FROM,
            Destination={'ToAddresses': EMAIL_TO},
            Message={
                'Subject': {
                    'Data': f'Relatório Diário de FinOps - {datetime.now().strftime("%d/%m/%Y")}',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_content,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        print(f"E-mail enviado com sucesso: {response['MessageId']}")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")


def lambda_handler(event, context):
    """
    Handler principal da função Lambda
    """
    print("Iniciando análise de FinOps...")
    
    # 1. Coletar dados de custo
    print("Coletando dados de custo...")
    cost_data = get_cost_and_usage(days=30)
    forecast_data = get_cost_forecast(days=30)
    
    # 2. Obter recomendações do Compute Optimizer
    print("Obtendo recomendações do Compute Optimizer...")
    compute_recommendations = get_compute_optimizer_recommendations()
    
    # 3. Obter verificações do Trusted Advisor
    print("Obtendo verificações do Trusted Advisor...")
    trusted_advisor_checks = get_trusted_advisor_checks()
    
    # 4. Identificar instâncias subutilizadas
    print("Identificando instâncias subutilizadas...")
    underutilized_instances = get_underutilized_ec2_instances()
    
    # 5. Analisar custos por serviço
    print("Analisando custos por serviço...")
    cost_summary = analyze_costs_by_service(cost_data)
    
    # 6. Gerar recomendações consolidadas
    print("Gerando recomendações de FinOps...")
    recommendations = generate_finops_recommendations(
        cost_data,
        compute_recommendations,
        trusted_advisor_checks,
        underutilized_instances
    )
    
    # 7. Formatar relatório HTML
    print("Formatando relatório...")
    html_report = format_html_report(cost_summary, forecast_data, recommendations)
    
    # 8. Salvar relatório no S3
    print("Salvando relatório no S3...")
    report_data = {
        'cost_summary': cost_summary,
        'forecast': forecast_data,
        'recommendations': recommendations
    }
    s3_key = save_report_to_s3(html_report, report_data)
    
    # 9. Salvar recomendações no DynamoDB
    print("Salvando recomendações no DynamoDB...")
    save_recommendations_to_dynamodb(recommendations)
    
    # 10. Enviar relatório por e-mail
    print("Enviando relatório por e-mail...")
    send_email_report(html_report)
    
    print("Análise de FinOps concluída com sucesso!")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'FinOps analysis completed successfully',
            's3_report': s3_key,
            'recommendations_count': len(recommendations)
        })
    }
