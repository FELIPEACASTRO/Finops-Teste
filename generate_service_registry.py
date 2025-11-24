#!/usr/bin/env python3
"""
Script para gerar automaticamente o registro completo de todos os 268 serviços AWS.
"""

from src.domain.entities.resource import ResourceType

# Template de metadados para cada serviço
SERVICE_TEMPLATES = {
    # COMPUTE
    "EC2": {"metrics": ["CPU", "Memory", "Network"], "opts": ["Right-sizing", "Reserved instances", "Spot instances"]},
    "LAMBDA": {"metrics": ["Invocations", "Duration"], "opts": ["Memory optimization", "Reserved concurrency"]},
    "ECS": {"metrics": ["CPU", "Memory", "Tasks"], "opts": ["Right-sizing", "Spot instances"]},
    "EKS": {"metrics": ["Node count", "Pod count"], "opts": ["Auto-scaling", "Node optimization"]},
    "FARGATE": {"metrics": ["Tasks", "vCPU"], "opts": ["Task right-sizing"]},
    "BATCH": {"metrics": ["Job count"], "opts": ["Job optimization"]},
    "LIGHTSAIL": {"metrics": ["Instances"], "opts": ["Right-sizing"]},
    "ELASTIC_BEANSTALK": {"metrics": ["Instances"], "opts": ["Environment optimization"]},
    "APP_RUNNER": {"metrics": ["Requests"], "opts": ["Auto-scaling tuning"]},
    "OUTPOSTS": {"metrics": ["Racks"], "opts": ["Capacity planning"]},
    
    # STORAGE
    "S3": {"metrics": ["Storage", "Requests"], "opts": ["Storage class", "Lifecycle policies"]},
    "EBS": {"metrics": ["Volume size", "IOPS"], "opts": ["Volume type", "Unused volumes"]},
    "EFS": {"metrics": ["Storage"], "opts": ["Performance mode"]},
    "FSX": {"metrics": ["Storage"], "opts": ["Throughput optimization"]},
    
    # DATABASE
    "RDS": {"metrics": ["CPU", "Memory", "Storage"], "opts": ["Right-sizing", "Reserved instances"]},
    "AURORA": {"metrics": ["CPU", "Connections"], "opts": ["Right-sizing", "Serverless"]},
    "DYNAMODB": {"metrics": ["Read capacity", "Write capacity"], "opts": ["On-demand mode", "TTL"]},
    "REDSHIFT": {"metrics": ["Nodes", "Storage"], "opts": ["Node optimization", "Pause cluster"]},
    
    # Add more as needed...
}

# Gerar nome amigável a partir do enum
def get_friendly_name(enum_name):
    """Converte SCREAMING_SNAKE_CASE para Title Case."""
    return enum_name.replace('_', ' ').title().replace('Aws', 'AWS').replace('Iot', 'IoT').replace('Ai', 'AI')

# Gerar metadados padrão
def generate_metadata(resource_type):
    """Gera metadados para um tipo de recurso."""
    name = resource_type.name
    
    # Se tem template específico, usa ele
    if name in SERVICE_TEMPLATES:
        return SERVICE_TEMPLATES[name]
    
    # Senão, gera metadados genéricos
    return {
        "metrics": ["Usage", "Requests"],
        "opts": ["Resource optimization", "Cost reduction"]
    }

# Contar serviços
services = [r for r in ResourceType if r not in [ResourceType.GENERIC, ResourceType.UNKNOWN]]
print(f"Total de serviços a serem registrados: {len(services)}")

# Gerar listagem por categoria
categories = {}
for service in services:
    # Detectar categoria pelo nome (simplificado)
    name = service.name
    if any(x in name for x in ['EC2', 'LAMBDA', 'ECS', 'EKS', 'BATCH', 'FARGATE', 'BEANSTALK', 'APP_RUNNER', 'LIGHTSAIL', 'OUTPOSTS']):
        cat = 'COMPUTE'
    elif any(x in name for x in ['S3', 'EBS', 'EFS', 'FSX', 'GLACIER', 'BACKUP', 'STORAGE']):
        cat = 'STORAGE'
    elif any(x in name for x in ['RDS', 'AURORA', 'DYNAMODB', 'REDSHIFT', 'NEPTUNE', 'DOCUMENTDB', 'ELASTICACHE', 'MEMORYDB', 'TIMESTREAM', 'QLDB', 'KEYSPACES', 'DAX']):
        cat = 'DATABASE'
    elif any(x in name for x in ['VPC', 'CLOUDFRONT', 'ROUTE53', 'DIRECT_CONNECT', 'ELB', 'ALB', 'NLB', 'API_GATEWAY', 'APP_MESH', 'TRANSIT_GATEWAY', 'PRIVATE_LINK', 'GLOBAL_ACCELERATOR', 'CLOUD_WAN']):
        cat = 'NETWORKING'
    elif any(x in name for x in ['ATHENA', 'EMR', 'KINESIS', 'MSK', 'GLUE', 'LAKE_FORMATION', 'QUICKSIGHT', 'OPENSEARCH', 'DATA_EXCHANGE', 'CLEAN_ROOMS', 'FINSPACE']):
        cat = 'ANALYTICS'
    elif any(x in name for x in ['SQS', 'SNS', 'SES', 'EVENTBRIDGE', 'STEP_FUNCTIONS', 'APPSYNC', 'MQ', 'APPFLOW']):
        cat = 'APPLICATION'
    elif any(x in name for x in ['SAGEMAKER', 'BEDROCK', 'TEXTRACT', 'REKOGNITION', 'COMPREHEND', 'TRANSLATE', 'POLLY', 'LEX', 'FORECAST', 'PERSONALIZE', 'FRAUD_DETECTOR', 'KENDRA', 'TRANSCRIBE', 'CODEWHISPERER', 'LOOKOUT', 'MONITRON', 'HEALTHLAKE', 'DEVOPS_GURU', 'AUGMENTED_AI', 'AMAZON_Q']):
        cat = 'AI_ML'
    elif any(x in name for x in ['CODE', 'CLOUD9', 'X_RAY', 'CLOUDSHELL', 'FAULT_INJECTION', 'PROTON', 'COPILOT']):
        cat = 'DEVELOPER_TOOLS'
    elif any(x in name for x in ['IAM', 'COGNITO', 'KMS', 'SECRETS_MANAGER', 'WAF', 'SHIELD', 'GUARDDUTY', 'MACIE', 'INSPECTOR', 'DETECTIVE', 'SECURITY', 'CERTIFICATE', 'CLOUDHSM', 'FIREWALL', 'VERIFIED', 'DIRECTORY', 'PAYMENT_CRYPTOGRAPHY', 'SIGNER', 'ARTIFACT', 'AUDIT']):
        cat = 'SECURITY'
    elif any(x in name for x in ['CLOUDWATCH', 'CLOUDTRAIL', 'CONFIG', 'SYSTEMS_MANAGER', 'CLOUDFORMATION', 'OPSWORKS', 'ORGANIZATIONS', 'CONTROL_TOWER', 'SERVICE_CATALOG', 'TRUSTED_ADVISOR', 'LICENSE_MANAGER', 'RESOURCE_GROUPS', 'TAG_EDITOR', 'GRAFANA', 'PROMETHEUS', 'CHATBOT', 'LAUNCH_WIZARD', 'RESILIENCE_HUB', 'INCIDENT_MANAGER']):
        cat = 'MANAGEMENT'
    elif any(x in name for x in ['MIGRATION', 'DMS', 'DATASYNC', 'TRANSFER_FAMILY', 'SNOW', 'MAINFRAME']):
        cat = 'MIGRATION'
    elif any(x in name for x in ['CONNECT', 'PINPOINT', 'CHIME', 'WORKMAIL', 'WORKDOCS', 'AMPLIFY', 'SUPPLY_CHAIN', 'WICKR', 'ALEXA']):
        cat = 'BUSINESS'
    elif any(x in name for x in ['WORKSPACES', 'APPSTREAM']):
        cat = 'END_USER_COMPUTING'
    elif any(x in name for x in ['IOT', 'FREERTOS']):
        cat = 'IOT'
    elif any(x in name for x in ['ROBO']):
        cat = 'ROBOTICS'
    elif any(x in name for x in ['MEDIA', 'ELASTIC_TRANSCODER', 'INTERACTIVE_VIDEO', 'NIMBLE']):
        cat = 'MEDIA'
    elif any(x in name for x in ['GAME', 'LUMBERYARD']):
        cat = 'GAME'
    elif any(x in name for x in ['SUMERIAN', 'AR_VR', 'SIMSPACE']):
        cat = 'AR_VR'
    elif any(x in name for x in ['BLOCKCHAIN', 'QUANTUM_LEDGER']):
        cat = 'BLOCKCHAIN'
    elif any(x in name for x in ['BRAKET']):
        cat = 'QUANTUM'
    elif any(x in name for x in ['GROUND_STATION']):
        cat = 'SATELLITE'
    elif any(x in name for x in ['COST', 'BUDGET', 'BILLING', 'SAVINGS', 'MARKETPLACE']):
        cat = 'COST_MANAGEMENT'
    elif any(x in name for x in ['IQ', 'SUPPORT', 'MANAGED_SERVICES']):
        cat = 'CUSTOMER_ENABLEMENT'
    else:
        cat = 'OTHER'
    
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(service)

# Exibir resumo
print("\nServiços por categoria:")
print("="*60)
for cat, servs in sorted(categories.items()):
    print(f"{cat:25s}: {len(servs):3d} serviços")
print("="*60)
print(f"{'TOTAL':25s}: {len(services):3d} serviços")

