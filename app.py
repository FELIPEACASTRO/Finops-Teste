#!/usr/bin/env python3
"""
Flask Web Interface for AWS FinOps Analyzer v4.0
Provides interactive web UI to explore the application capabilities
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime
import json
from src.infrastructure.aws.aws_service_registry import (
    AWS_SERVICE_REGISTRY,
    get_all_categories,
    get_services_by_category,
    get_service_info,
    get_total_services_count
)
from src.domain.entities import ResourceType

app = Flask(__name__)


@app.route('/')
def index():
    """Main page with project overview"""
    return render_template('index.html')


@app.route('/api/services')
def get_services():
    """Get all AWS services grouped by category"""
    categories_data = {}
    
    for category in get_all_categories():
        services = get_services_by_category(category)
        categories_data[category.value] = [
            {
                'type': service.value,
                'info': {
                    'name': get_service_info(service)['name'],
                    'category': get_service_info(service)['category'].value,
                    'metrics': get_service_info(service)['metrics'],
                    'optimization_opportunities': get_service_info(service)['optimization_opportunities']
                }
            }
            for service in services
        ]
    
    return jsonify({
        'total_services': get_total_services_count(),
        'total_categories': len(get_all_categories()),
        'categories': categories_data
    })


@app.route('/api/service/<service_type>')
def get_service_details(service_type):
    """Get details for a specific service"""
    try:
        resource_type = ResourceType(service_type)
        info = get_service_info(resource_type)
        return jsonify({
            'service_type': service_type,
            'name': info['name'],
            'category': info['category'].value,
            'metrics': info['metrics'],
            'optimization_opportunities': info['optimization_opportunities']
        })
    except ValueError:
        return jsonify({'error': 'Service not found'}), 404


@app.route('/api/stats')
def get_stats():
    """Get project statistics"""
    return jsonify({
        'version': '4.0',
        'total_services': get_total_services_count(),
        'categories': len(get_all_categories()),
        'tests_passing': 386,
        'code_coverage': '42%',
        'architecture': 'Clean Architecture + DDD',
        'ai_model': 'Amazon Bedrock (Claude 3 Sonnet)',
        'status': 'Production Ready'
    })


@app.route('/api/demo-analysis')
def demo_analysis():
    """Get demo analysis output"""
    return jsonify({
        'generated_at': datetime.now().isoformat() + 'Z',
        'version': '4.0-bedrock',
        'model_used': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'analysis_period_days': 30,
        'resources_analyzed': 247,
        'regions': ['us-east-1', 'us-west-2', 'eu-west-1'],
        'summary': {
            'total_monthly_savings_usd': 3456.78,
            'total_annual_savings_usd': 41481.36,
            'high_priority_actions': 12,
            'medium_priority_actions': 23,
            'low_priority_actions': 8
        },
        'top_recommendations': [
            {
                'resource_type': 'EC2',
                'resource_id': 'i-0a1b2c3d4e5f6g7h8',
                'region': 'us-east-1',
                'current_config': 't3a.xlarge (4 vCPU, 16GB RAM)',
                'recommendation': {
                    'action': 'downsize',
                    'details': 'Downsize from t3a.xlarge to t3a.large',
                    'reasoning': 'CPU avg 18.5%, p95 28.7% - 75% capacity unused'
                },
                'didactic_explanation': 'Sua instância EC2 está usando muito menos memória e poder de processamento do que o disponível. Isso significa que você está pagando por recursos que não está usando. Ao reduzir o tamanho, você mantém a mesma performance mas reduz significativamente os custos.',
                'technical_steps': [
                    'Crie um snapshot da AMI atual para backup seguro',
                    'Pause a aplicação ou ative load balancer para direcionar tráfego',
                    'Interrompa a instância atual',
                    'Inicie uma nova instância t3a.large a partir do mesmo snapshot',
                    'Configure os mesmos grupos de segurança e subnets',
                    'Teste a aplicação completamente antes de remover a instância antiga',
                    'Após validação, remova a instância t3a.xlarge para parar os custos'
                ],
                'savings': {
                    'monthly_usd': 54.74,
                    'annual_usd': 656.88,
                    'percentage': 50
                },
                'risk_level': 'low',
                'priority': 'high'
            },
            {
                'resource_type': 'RDS',
                'resource_id': 'mydb-instance-1',
                'region': 'us-east-1',
                'current_config': 'db.m5.large (MySQL 8.0)',
                'recommendation': {
                    'action': 'reserved_instance',
                    'details': 'Purchase 1-year Reserved Instance',
                    'reasoning': 'Database running 24/7 for 6+ months'
                },
                'didactic_explanation': 'Seu banco de dados está sempre ligado e não varia em uso. Isso é o cenário perfeito para Reserved Instances. É como assinar um plano anual ao invés de pagar por hora - você economiza muito pagando adiantado por um período que você já sabe que vai usar.',
                'technical_steps': [
                    'Verifique no console RDS que a instância é elegível para Reserved Instance',
                    'Acesse AWS Cost Explorer para confirmar o histórico de uso contínuo',
                    'Vá até o console de Compra de Reserved Instances no RDS',
                    'Selecione: Tipo db.m5.large, região us-east-1, período 1 ano',
                    'Escolha pagamento full upfront para máxima economia',
                    'Revise a estimativa e confirme a compra',
                    'O desconto será aplicado automaticamente nas próximas faturas'
                ],
                'savings': {
                    'monthly_usd': 89.32,
                    'annual_usd': 1071.84,
                    'percentage': 40
                },
                'risk_level': 'low',
                'priority': 'high'
            },
            {
                'resource_type': 'S3',
                'resource_id': 'my-archive-bucket',
                'region': 'us-west-2',
                'current_config': 'Standard storage (2.5 TB)',
                'recommendation': {
                    'action': 'storage_class_change',
                    'details': 'Move to S3 Intelligent-Tiering',
                    'reasoning': '67% of objects not accessed in 90+ days'
                },
                'didactic_explanation': 'A maioria dos seus arquivos não é acessada regularmente. Você está pagando preço premium (Standard) mesmo quando os dados não são usados. S3 Intelligent-Tiering move automaticamente dados antigos para classes mais baratas, mantendo os frequentes rápidos. É como ter dois preços automáticos baseados no uso real.',
                'technical_steps': [
                    'Acesse o console do S3 e selecione o bucket my-archive-bucket',
                    'Vá em "Management" → "Lifecycle rules"',
                    'Clique em "Create lifecycle rule"',
                    'Nome: "archive-old-files"',
                    'Aplique para todos os objetos (ou selecione prefixo específico)',
                    'Em "Transitions": selecione "Transition to Intelligent-Tiering" em 30 dias',
                    'Salve a regra',
                    'Monitore custo em Cloud Watch Metrics após 60 dias'
                ],
                'savings': {
                    'monthly_usd': 37.50,
                    'annual_usd': 450.00,
                    'percentage': 60
                },
                'risk_level': 'low',
                'priority': 'medium'
            }
        ],
        'category_breakdown': {
            'Compute': {'count': 45, 'monthly_savings': 890.25},
            'Storage': {'count': 67, 'monthly_savings': 456.80},
            'Database': {'count': 23, 'monthly_savings': 1234.50},
            'Networking': {'count': 34, 'monthly_savings': 345.60},
            'Other': {'count': 78, 'monthly_savings': 529.63}
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
