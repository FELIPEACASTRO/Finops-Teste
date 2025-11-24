"""AWS Service Registry - Metadata for all supported AWS services."""

from typing import Dict, List
from enum import Enum
from ...domain.entities import ResourceType


class ServiceCategory(Enum):
    """AWS service categories."""
    COMPUTE = "Compute"
    STORAGE = "Storage"
    DATABASE = "Database"
    NETWORKING = "Networking"
    ANALYTICS = "Analytics"
    APPLICATION = "Application Services"
    AI_ML = "AI/ML"
    DEVELOPER_TOOLS = "Developer Tools"
    SECURITY = "Security & Identity"
    MANAGEMENT = "Management & Governance"
    ENTERPRISE = "Enterprise & End User Computing"


# Service metadata registry - 80+ AWS services
AWS_SERVICE_REGISTRY: Dict[ResourceType, Dict] = {
    # COMPUTE (7 services)
    ResourceType.EC2: {"category": ServiceCategory.COMPUTE, "name": "Elastic Compute Cloud", "metrics": ["CPU", "Memory", "Network", "Disk I/O"], "optimization_opportunities": ["Right-sizing", "Reserved instances", "Spot instances"]},
    ResourceType.LAMBDA: {"category": ServiceCategory.COMPUTE, "name": "Lambda", "metrics": ["Invocations", "Duration", "Errors"], "optimization_opportunities": ["Memory optimization", "Reserved concurrency"]},
    ResourceType.ECS: {"category": ServiceCategory.COMPUTE, "name": "Elastic Container Service", "metrics": ["CPU", "Memory", "Task count"], "optimization_opportunities": ["Right-sizing tasks", "Spot instances"]},
    ResourceType.EKS: {"category": ServiceCategory.COMPUTE, "name": "Elastic Kubernetes Service", "metrics": ["Node count", "Pod count"], "optimization_opportunities": ["Node right-sizing", "Auto-scaling"]},
    ResourceType.BATCH: {"category": ServiceCategory.COMPUTE, "name": "Batch", "metrics": ["Job count"], "optimization_opportunities": ["Job optimization", "Instance selection"]},
    ResourceType.LIGHTSAIL: {"category": ServiceCategory.COMPUTE, "name": "Lightsail", "metrics": ["Instances", "Bandwidth"], "optimization_opportunities": ["Right-sizing"]},
    ResourceType.APPSTREAM: {"category": ServiceCategory.COMPUTE, "name": "AppStream", "metrics": ["Instance hours"], "optimization_opportunities": ["Capacity optimization"]},
    
    # STORAGE (7 services)
    ResourceType.S3: {"category": ServiceCategory.STORAGE, "name": "Simple Storage Service", "metrics": ["Storage size", "Requests"], "optimization_opportunities": ["Storage class analysis", "Lifecycle policies", "Data transfer"]},
    ResourceType.EBS: {"category": ServiceCategory.STORAGE, "name": "Elastic Block Store", "metrics": ["Volume size", "IOPS"], "optimization_opportunities": ["Volume type optimization", "Unattached volumes"]},
    ResourceType.EFS: {"category": ServiceCategory.STORAGE, "name": "Elastic File System", "metrics": ["Storage size"], "optimization_opportunities": ["Performance class optimization"]},
    ResourceType.FSX: {"category": ServiceCategory.STORAGE, "name": "FSx", "metrics": ["Storage capacity"], "optimization_opportunities": ["Throughput optimization"]},
    ResourceType.GLACIER: {"category": ServiceCategory.STORAGE, "name": "Glacier", "metrics": ["Archive count", "Storage"], "optimization_opportunities": ["Retrieval optimization"]},
    ResourceType.STORAGE_GATEWAY: {"category": ServiceCategory.STORAGE, "name": "Storage Gateway", "metrics": ["Data transferred"], "optimization_opportunities": ["Gateway type optimization"]},
    ResourceType.BACKUP: {"category": ServiceCategory.STORAGE, "name": "Backup", "metrics": ["Backup size", "Recovery points"], "optimization_opportunities": ["Retention policy tuning"]},
    
    # DATABASE (10 services)
    ResourceType.RDS: {"category": ServiceCategory.DATABASE, "name": "Relational Database Service", "metrics": ["CPU", "Memory", "Storage"], "optimization_opportunities": ["Instance right-sizing", "Reserved instances"]},
    ResourceType.DYNAMODB: {"category": ServiceCategory.DATABASE, "name": "DynamoDB", "metrics": ["Read capacity", "Write capacity"], "optimization_opportunities": ["On-demand vs provisioned", "TTL setup"]},
    ResourceType.ELASTICACHE: {"category": ServiceCategory.DATABASE, "name": "ElastiCache", "metrics": ["Node type", "Memory"], "optimization_opportunities": ["Node right-sizing"]},
    ResourceType.REDSHIFT: {"category": ServiceCategory.DATABASE, "name": "Redshift", "metrics": ["Nodes", "Storage"], "optimization_opportunities": ["Node type optimization", "Pause cluster"]},
    ResourceType.DOCUMENTDB: {"category": ServiceCategory.DATABASE, "name": "DocumentDB", "metrics": ["Instances", "Storage"], "optimization_opportunities": ["Instance right-sizing"]},
    ResourceType.NEPTUNE: {"category": ServiceCategory.DATABASE, "name": "Neptune", "metrics": ["Instances"], "optimization_opportunities": ["Instance type optimization"]},
    ResourceType.QLDB: {"category": ServiceCategory.DATABASE, "name": "QLDB", "metrics": ["Ledger entries"], "optimization_opportunities": ["Journal lifecycle"]},
    ResourceType.TIMESTREAM: {"category": ServiceCategory.DATABASE, "name": "Timestream", "metrics": ["Data stored"], "optimization_opportunities": ["Memory retention tuning"]},
    ResourceType.DAX: {"category": ServiceCategory.DATABASE, "name": "DAX", "metrics": ["Nodes", "Cache"], "optimization_opportunities": ["Node right-sizing"]},
    ResourceType.MEMORYDB: {"category": ServiceCategory.DATABASE, "name": "MemoryDB", "metrics": ["Nodes", "Memory"], "optimization_opportunities": ["Node type optimization"]},
    
    # NETWORKING (10 services)
    ResourceType.ELB: {"category": ServiceCategory.NETWORKING, "name": "Elastic Load Balancing", "metrics": ["Connections"], "optimization_opportunities": ["Unused load balancers"]},
    ResourceType.ALB: {"category": ServiceCategory.NETWORKING, "name": "Application Load Balancer", "metrics": ["Requests"], "optimization_opportunities": ["Unused ALBs"]},
    ResourceType.NLB: {"category": ServiceCategory.NETWORKING, "name": "Network Load Balancer", "metrics": ["Connections"], "optimization_opportunities": ["Unused NLBs"]},
    ResourceType.CLOUDFRONT: {"category": ServiceCategory.NETWORKING, "name": "CloudFront", "metrics": ["Requests", "Data transfer"], "optimization_opportunities": ["Cache optimization"]},
    ResourceType.ROUTE53: {"category": ServiceCategory.NETWORKING, "name": "Route 53", "metrics": ["Queries"], "optimization_opportunities": ["Unused hosted zones"]},
    ResourceType.VPC: {"category": ServiceCategory.NETWORKING, "name": "Virtual Private Cloud", "metrics": ["NAT usage"], "optimization_opportunities": ["NAT gateway optimization"]},
    ResourceType.DIRECT_CONNECT: {"category": ServiceCategory.NETWORKING, "name": "Direct Connect", "metrics": ["Ports"], "optimization_opportunities": ["Port optimization"]},
    ResourceType.TRANSIT_GATEWAY: {"category": ServiceCategory.NETWORKING, "name": "Transit Gateway", "metrics": ["Bytes processed"], "optimization_opportunities": ["Attachment consolidation"]},
    ResourceType.PRIVATE_LINK: {"category": ServiceCategory.NETWORKING, "name": "PrivateLink", "metrics": ["Connections"], "optimization_opportunities": ["Unused endpoints"]},
    ResourceType.APP_MESH: {"category": ServiceCategory.NETWORKING, "name": "App Mesh", "metrics": ["Virtual nodes"], "optimization_opportunities": ["Resource consolidation"]},
    
    # ANALYTICS (7 services)
    ResourceType.ATHENA: {"category": ServiceCategory.ANALYTICS, "name": "Athena", "metrics": ["Queries", "Data scanned"], "optimization_opportunities": ["Query optimization"]},
    ResourceType.EMR: {"category": ServiceCategory.ANALYTICS, "name": "Elastic MapReduce", "metrics": ["Instance hours"], "optimization_opportunities": ["Instance right-sizing"]},
    ResourceType.KINESIS: {"category": ServiceCategory.ANALYTICS, "name": "Kinesis", "metrics": ["Shards"], "optimization_opportunities": ["Shard optimization"]},
    ResourceType.MSK: {"category": ServiceCategory.ANALYTICS, "name": "MSK", "metrics": ["Brokers"], "optimization_opportunities": ["Broker optimization"]},
    ResourceType.GLUE: {"category": ServiceCategory.ANALYTICS, "name": "Glue", "metrics": ["DPU hours"], "optimization_opportunities": ["DPU optimization"]},
    ResourceType.DATA_PIPELINE: {"category": ServiceCategory.ANALYTICS, "name": "Data Pipeline", "metrics": ["Nodes"], "optimization_opportunities": ["Right-sizing"]},
    ResourceType.LAKE_FORMATION: {"category": ServiceCategory.ANALYTICS, "name": "Lake Formation", "metrics": ["Storage"], "optimization_opportunities": ["Data lifecycle"]},
    
    # APPLICATION SERVICES (9 services)
    ResourceType.SQS: {"category": ServiceCategory.APPLICATION, "name": "Simple Queue Service", "metrics": ["Messages"], "optimization_opportunities": ["Queue consolidation"]},
    ResourceType.SNS: {"category": ServiceCategory.APPLICATION, "name": "Simple Notification Service", "metrics": ["Messages"], "optimization_opportunities": ["Topic consolidation"]},
    ResourceType.SES: {"category": ServiceCategory.APPLICATION, "name": "Simple Email Service", "metrics": ["Emails sent"], "optimization_opportunities": ["Bounce optimization"]},
    ResourceType.APPSYNC: {"category": ServiceCategory.APPLICATION, "name": "AppSync", "metrics": ["Requests"], "optimization_opportunities": ["Query optimization"]},
    ResourceType.EVENTBRIDGE: {"category": ServiceCategory.APPLICATION, "name": "EventBridge", "metrics": ["Events"], "optimization_opportunities": ["Rule consolidation"]},
    ResourceType.STEP_FUNCTIONS: {"category": ServiceCategory.APPLICATION, "name": "Step Functions", "metrics": ["Executions"], "optimization_opportunities": ["Workflow optimization"]},
    ResourceType.AMPLIFY: {"category": ServiceCategory.APPLICATION, "name": "Amplify", "metrics": ["Builds", "Build minutes"], "optimization_opportunities": ["Build optimization"]},
    ResourceType.APPCONFIG: {"category": ServiceCategory.APPLICATION, "name": "AppConfig", "metrics": ["Config profiles"], "optimization_opportunities": ["Configuration consolidation"]},
    ResourceType.SERVICE_DISCOVERY: {"category": ServiceCategory.APPLICATION, "name": "Service Discovery", "metrics": ["Services"], "optimization_opportunities": ["Service consolidation"]},
    
    # AI/ML (10 services)
    ResourceType.SAGEMAKER: {"category": ServiceCategory.AI_ML, "name": "SageMaker", "metrics": ["Instance hours"], "optimization_opportunities": ["Spot training"]},
    ResourceType.TEXTRACT: {"category": ServiceCategory.AI_ML, "name": "Textract", "metrics": ["Documents processed"], "optimization_opportunities": ["Batch optimization"]},
    ResourceType.REKOGNITION: {"category": ServiceCategory.AI_ML, "name": "Rekognition", "metrics": ["API calls"], "optimization_opportunities": ["API call optimization"]},
    ResourceType.COMPREHEND: {"category": ServiceCategory.AI_ML, "name": "Comprehend", "metrics": ["Units"], "optimization_opportunities": ["Batch optimization"]},
    ResourceType.TRANSLATE: {"category": ServiceCategory.AI_ML, "name": "Translate", "metrics": ["Characters"], "optimization_opportunities": ["Batch translation"]},
    ResourceType.POLLY: {"category": ServiceCategory.AI_ML, "name": "Polly", "metrics": ["Characters"], "optimization_opportunities": ["Cache optimization"]},
    ResourceType.LEX: {"category": ServiceCategory.AI_ML, "name": "Lex", "metrics": ["Requests"], "optimization_opportunities": ["Request optimization"]},
    ResourceType.FORECAST: {"category": ServiceCategory.AI_ML, "name": "Forecast", "metrics": ["Forecasts"], "optimization_opportunities": ["Forecast optimization"]},
    ResourceType.LOOKOUT: {"category": ServiceCategory.AI_ML, "name": "Lookout", "metrics": ["Detections"], "optimization_opportunities": ["Detection optimization"]},
    ResourceType.BEDROCK: {"category": ServiceCategory.AI_ML, "name": "Bedrock", "metrics": ["Invocations", "Tokens"], "optimization_opportunities": ["Model selection"]},
    
    # DEVELOPER TOOLS (9 services)
    ResourceType.CODEBUILD: {"category": ServiceCategory.DEVELOPER_TOOLS, "name": "CodeBuild", "metrics": ["Build minutes"], "optimization_opportunities": ["Build optimization"]},
    ResourceType.CODEPIPELINE: {"category": ServiceCategory.DEVELOPER_TOOLS, "name": "CodePipeline", "metrics": ["Pipelines"], "optimization_opportunities": ["Pipeline consolidation"]},
    ResourceType.CODEDEPLOY: {"category": ServiceCategory.DEVELOPER_TOOLS, "name": "CodeDeploy", "metrics": ["Deployments"], "optimization_opportunities": ["Deployment consolidation"]},
    ResourceType.CODECOMMIT: {"category": ServiceCategory.DEVELOPER_TOOLS, "name": "CodeCommit", "metrics": ["Repositories"], "optimization_opportunities": ["Repo consolidation"]},
    ResourceType.CLOUDFORMATION: {"category": ServiceCategory.DEVELOPER_TOOLS, "name": "CloudFormation", "metrics": ["Stacks"], "optimization_opportunities": ["Stack consolidation"]},
    ResourceType.OPSWORKS: {"category": ServiceCategory.DEVELOPER_TOOLS, "name": "OpsWorks", "metrics": ["Stacks"], "optimization_opportunities": ["Stack consolidation"]},
    ResourceType.SYSTEMS_MANAGER: {"category": ServiceCategory.DEVELOPER_TOOLS, "name": "Systems Manager", "metrics": ["Managed nodes"], "optimization_opportunities": ["Node consolidation"]},
    ResourceType.CLOUDWATCH: {"category": ServiceCategory.DEVELOPER_TOOLS, "name": "CloudWatch", "metrics": ["Logs", "Metrics"], "optimization_opportunities": ["Log retention tuning"]},
    ResourceType.X_RAY: {"category": ServiceCategory.DEVELOPER_TOOLS, "name": "X-Ray", "metrics": ["Traces"], "optimization_opportunities": ["Trace sampling"]},
    
    # SECURITY (14 services)
    ResourceType.IAM: {"category": ServiceCategory.SECURITY, "name": "IAM", "metrics": ["Users", "Roles"], "optimization_opportunities": ["User/role consolidation"]},
    ResourceType.COGNITO: {"category": ServiceCategory.SECURITY, "name": "Cognito", "metrics": ["Users", "MAU"], "optimization_opportunities": ["User pool consolidation"]},
    ResourceType.SECRETS_MANAGER: {"category": ServiceCategory.SECURITY, "name": "Secrets Manager", "metrics": ["Secrets"], "optimization_opportunities": ["Secret consolidation"]},
    ResourceType.KMS: {"category": ServiceCategory.SECURITY, "name": "KMS", "metrics": ["Keys"], "optimization_opportunities": ["Key consolidation"]},
    ResourceType.CLOUDHSM: {"category": ServiceCategory.SECURITY, "name": "CloudHSM", "metrics": ["HSMs"], "optimization_opportunities": ["HSM consolidation"]},
    ResourceType.CERTIFICATE_MANAGER: {"category": ServiceCategory.SECURITY, "name": "Certificate Manager", "metrics": ["Certificates"], "optimization_opportunities": ["Cert consolidation"]},
    ResourceType.WAF: {"category": ServiceCategory.SECURITY, "name": "WAF", "metrics": ["Rules"], "optimization_opportunities": ["Rule consolidation"]},
    ResourceType.SHIELD: {"category": ServiceCategory.SECURITY, "name": "Shield", "metrics": ["Protected resources"], "optimization_opportunities": ["Resource consolidation"]},
    ResourceType.GUARDDUTY: {"category": ServiceCategory.SECURITY, "name": "GuardDuty", "metrics": ["Findings"], "optimization_opportunities": ["Finding suppression"]},
    ResourceType.MACIE: {"category": ServiceCategory.SECURITY, "name": "Macie", "metrics": ["Buckets"], "optimization_opportunities": ["Bucket consolidation"]},
    ResourceType.INSPECTOR: {"category": ServiceCategory.SECURITY, "name": "Inspector", "metrics": ["Assessments"], "optimization_opportunities": ["Assessment consolidation"]},
    ResourceType.AUDIT_MANAGER: {"category": ServiceCategory.SECURITY, "name": "Audit Manager", "metrics": ["Assessments"], "optimization_opportunities": ["Assessment consolidation"]},
    ResourceType.SECURITY_HUB: {"category": ServiceCategory.SECURITY, "name": "Security Hub", "metrics": ["Findings"], "optimization_opportunities": ["Finding consolidation"]},
    ResourceType.RESOURCE_ACCESS_MANAGER: {"category": ServiceCategory.SECURITY, "name": "Resource Access Manager", "metrics": ["Shares"], "optimization_opportunities": ["Share consolidation"]},
}


def get_service_info(resource_type: ResourceType) -> Dict:
    """Get metadata for a service."""
    return AWS_SERVICE_REGISTRY.get(
        resource_type,
        {
            "category": ServiceCategory.MANAGEMENT,
            "name": resource_type.value,
            "metrics": [],
            "optimization_opportunities": [],
        }
    )


def get_services_by_category(category: ServiceCategory) -> List[ResourceType]:
    """Get all services in a category."""
    return [
        service_type
        for service_type, info in AWS_SERVICE_REGISTRY.items()
        if info.get("category") == category
    ]


def get_all_categories() -> List[ServiceCategory]:
    """Get all service categories."""
    categories = set()
    for info in AWS_SERVICE_REGISTRY.values():
        categories.add(info.get("category", ServiceCategory.MANAGEMENT))
    return sorted(list(categories), key=lambda x: x.value)
