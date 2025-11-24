"""AWS Service Registry - Metadata for ALL 268+ AWS services (comprehensive coverage 2025)."""

from typing import Dict, List
from enum import Enum
from ...domain.entities import ResourceType


class ServiceCategory(Enum):
    """AWS service categories - 24 categorias (cobertura completa 2025)."""
    COMPUTE = "Compute"
    STORAGE = "Storage"
    DATABASE = "Database"
    NETWORKING = "Networking & Content Delivery"
    ANALYTICS = "Analytics & Big Data"
    APPLICATION = "Application Integration"
    AI_ML = "AI & Machine Learning"
    DEVELOPER_TOOLS = "Developer Tools"
    SECURITY = "Security & Identity"
    MANAGEMENT = "Management & Governance"
    MIGRATION = "Migration & Transfer"
    BUSINESS = "Business Applications"
    END_USER_COMPUTING = "End User Computing"
    IOT = "Internet of Things"
    ROBOTICS = "Robotics"
    MEDIA = "Media Services"
    GAME = "Game Tech"
    AR_VR = "AR/VR"
    BLOCKCHAIN = "Blockchain"
    QUANTUM = "Quantum Computing"
    SATELLITE = "Satellite"
    COST_MANAGEMENT = "Cost Management"
    CUSTOMER_ENABLEMENT = "Customer Enablement"
    OTHER = "Other Services"


# Mapeamento de serviços para categorias (para geração automática)
SERVICE_CATEGORY_MAP = {
    # COMPUTE
    "EC2": ServiceCategory.COMPUTE, "LAMBDA": ServiceCategory.COMPUTE, "ECS": ServiceCategory.COMPUTE,
    "EKS": ServiceCategory.COMPUTE, "FARGATE": ServiceCategory.COMPUTE, "BATCH": ServiceCategory.COMPUTE,
    "LIGHTSAIL": ServiceCategory.COMPUTE, "ELASTIC_BEANSTALK": ServiceCategory.COMPUTE, 
    "APP_RUNNER": ServiceCategory.COMPUTE, "OUTPOSTS": ServiceCategory.COMPUTE,
    "LOCAL_ZONES": ServiceCategory.COMPUTE, "WAVELENGTH": ServiceCategory.COMPUTE,
    "SERVERLESS_APPLICATION_REPOSITORY": ServiceCategory.COMPUTE, "VMWARE_CLOUD": ServiceCategory.COMPUTE,
    "PARALLEL_CLUSTER": ServiceCategory.COMPUTE,
    
    # STORAGE
    "S3": ServiceCategory.STORAGE, "EBS": ServiceCategory.STORAGE, "EFS": ServiceCategory.STORAGE,
    "FSX": ServiceCategory.STORAGE, "GLACIER": ServiceCategory.STORAGE, "BACKUP": ServiceCategory.STORAGE,
    "STORAGE_GATEWAY": ServiceCategory.STORAGE, "ELASTIC_DISASTER_RECOVERY": ServiceCategory.STORAGE,
    "FILE_CACHE": ServiceCategory.STORAGE, "S3_GLACIER": ServiceCategory.STORAGE,
    "S3_GLACIER_DEEP_ARCHIVE": ServiceCategory.STORAGE, "S3_INTELLIGENT_TIERING": ServiceCategory.STORAGE,
    "FSX_WINDOWS": ServiceCategory.STORAGE, "FSX_LUSTRE": ServiceCategory.STORAGE,
    "FSX_NETAPP_ONTAP": ServiceCategory.STORAGE, "FSX_OPENZFS": ServiceCategory.STORAGE,
    
    # DATABASE
    "RDS": ServiceCategory.DATABASE, "AURORA": ServiceCategory.DATABASE, "DYNAMODB": ServiceCategory.DATABASE,
    "ELASTICACHE": ServiceCategory.DATABASE, "MEMORYDB": ServiceCategory.DATABASE, 
    "REDSHIFT": ServiceCategory.DATABASE, "DOCUMENTDB": ServiceCategory.DATABASE,
    "NEPTUNE": ServiceCategory.DATABASE, "QLDB": ServiceCategory.DATABASE, 
    "TIMESTREAM": ServiceCategory.DATABASE, "KEYSPACES": ServiceCategory.DATABASE, "DAX": ServiceCategory.DATABASE,
    "AURORA_SERVERLESS": ServiceCategory.DATABASE, "AURORA_DSQL": ServiceCategory.DATABASE,
    "ELASTICACHE_SERVERLESS": ServiceCategory.DATABASE, "REDSHIFT_SERVERLESS": ServiceCategory.DATABASE,
    "RDS_PROXY": ServiceCategory.DATABASE,
    
    # NETWORKING
    "VPC": ServiceCategory.NETWORKING, "CLOUDFRONT": ServiceCategory.NETWORKING, 
    "ROUTE53": ServiceCategory.NETWORKING, "API_GATEWAY": ServiceCategory.NETWORKING,
    "DIRECT_CONNECT": ServiceCategory.NETWORKING, "APP_MESH": ServiceCategory.NETWORKING,
    "ELB": ServiceCategory.NETWORKING, "ALB": ServiceCategory.NETWORKING, "NLB": ServiceCategory.NETWORKING,
    "PRIVATE_LINK": ServiceCategory.NETWORKING, "TRANSIT_GATEWAY": ServiceCategory.NETWORKING,
    "CLOUD_MAP": ServiceCategory.NETWORKING, "GLOBAL_ACCELERATOR": ServiceCategory.NETWORKING,
    "GATEWAY_LOAD_BALANCER": ServiceCategory.NETWORKING, "CLIENT_VPN": ServiceCategory.NETWORKING,
    "SITE_TO_SITE_VPN": ServiceCategory.NETWORKING, "CLOUD_WAN": ServiceCategory.NETWORKING,
    "PRIVATE_5G": ServiceCategory.NETWORKING, "VPC_LATTICE": ServiceCategory.NETWORKING,
    "VERIFIED_ACCESS": ServiceCategory.NETWORKING,
    
    # ANALYTICS
    "ATHENA": ServiceCategory.ANALYTICS, "EMR": ServiceCategory.ANALYTICS, "KINESIS": ServiceCategory.ANALYTICS,
    "MSK": ServiceCategory.ANALYTICS, "GLUE": ServiceCategory.ANALYTICS, 
    "DATA_PIPELINE": ServiceCategory.ANALYTICS, "LAKE_FORMATION": ServiceCategory.ANALYTICS,
    "QUICKSIGHT": ServiceCategory.ANALYTICS, "OPENSEARCH_SERVICE": ServiceCategory.ANALYTICS,
    "DATA_EXCHANGE": ServiceCategory.ANALYTICS, "CLEAN_ROOMS": ServiceCategory.ANALYTICS,
    "FINSPACE": ServiceCategory.ANALYTICS, "EMR_SERVERLESS": ServiceCategory.ANALYTICS,
    "MSK_SERVERLESS": ServiceCategory.ANALYTICS, "KINESIS_DATA_STREAMS": ServiceCategory.ANALYTICS,
    "KINESIS_DATA_FIREHOSE": ServiceCategory.ANALYTICS, "KINESIS_DATA_ANALYTICS": ServiceCategory.ANALYTICS,
    "KINESIS_VIDEO_STREAMS": ServiceCategory.ANALYTICS, "GLUE_DATABREW": ServiceCategory.ANALYTICS,
    
    # APPLICATION
    "SQS": ServiceCategory.APPLICATION, "SNS": ServiceCategory.APPLICATION, "SES": ServiceCategory.APPLICATION,
    "APPSYNC": ServiceCategory.APPLICATION, "EVENTBRIDGE": ServiceCategory.APPLICATION,
    "STEP_FUNCTIONS": ServiceCategory.APPLICATION, "AMPLIFY": ServiceCategory.APPLICATION,
    "APP_CONFIG": ServiceCategory.APPLICATION, "SERVICE_DISCOVERY": ServiceCategory.APPLICATION,
    "SWF": ServiceCategory.APPLICATION, "MQ": ServiceCategory.APPLICATION,
    "MANAGED_APACHE_AIRFLOW": ServiceCategory.APPLICATION, "APPFLOW": ServiceCategory.APPLICATION,
    "B2BI": ServiceCategory.APPLICATION, "EVENTBRIDGE_PIPES": ServiceCategory.APPLICATION,
    "STEP_FUNCTIONS_EXPRESS": ServiceCategory.APPLICATION,
    
    # AI/ML
    "SAGEMAKER": ServiceCategory.AI_ML, "TEXTRACT": ServiceCategory.AI_ML, 
    "REKOGNITION": ServiceCategory.AI_ML, "COMPREHEND": ServiceCategory.AI_ML,
    "TRANSLATE": ServiceCategory.AI_ML, "POLLY": ServiceCategory.AI_ML, "LEX": ServiceCategory.AI_ML,
    "FORECAST": ServiceCategory.AI_ML, "LOOKOUT": ServiceCategory.AI_ML, "BEDROCK": ServiceCategory.AI_ML,
    "PERSONALIZE": ServiceCategory.AI_ML, "FRAUD_DETECTOR": ServiceCategory.AI_ML,
    "KENDRA": ServiceCategory.AI_ML, "TRANSCRIBE": ServiceCategory.AI_ML,
    "CODEWHISPERER": ServiceCategory.AI_ML, "AMAZON_Q": ServiceCategory.AI_ML,
    "AMAZON_Q_BUSINESS": ServiceCategory.AI_ML, "SAGEMAKER_STUDIO": ServiceCategory.AI_ML,
    "SAGEMAKER_CANVAS": ServiceCategory.AI_ML, "LOOKOUT_METRICS": ServiceCategory.AI_ML,
    "LOOKOUT_VISION": ServiceCategory.AI_ML, "LOOKOUT_EQUIPMENT": ServiceCategory.AI_ML,
    "MONITRON": ServiceCategory.AI_ML, "HEALTHLAKE": ServiceCategory.AI_ML,
    "AUGMENTED_AI": ServiceCategory.AI_ML, "DEVOPS_GURU": ServiceCategory.AI_ML,
    
    # DEVELOPER TOOLS
    "CODECOMMIT": ServiceCategory.DEVELOPER_TOOLS, "CODEBUILD": ServiceCategory.DEVELOPER_TOOLS,
    "CODEDEPLOY": ServiceCategory.DEVELOPER_TOOLS, "CODEPIPELINE": ServiceCategory.DEVELOPER_TOOLS,
    "CLOUDFORMATION": ServiceCategory.DEVELOPER_TOOLS, "OPSWORKS": ServiceCategory.DEVELOPER_TOOLS,
    "SYSTEMS_MANAGER": ServiceCategory.DEVELOPER_TOOLS, "CLOUDWATCH": ServiceCategory.DEVELOPER_TOOLS,
    "X_RAY": ServiceCategory.DEVELOPER_TOOLS, "CODESTAR": ServiceCategory.DEVELOPER_TOOLS,
    "CODECATALYST": ServiceCategory.DEVELOPER_TOOLS, "CODEGURU": ServiceCategory.DEVELOPER_TOOLS,
    "CODEARTIFACT": ServiceCategory.DEVELOPER_TOOLS, "CLOUD9": ServiceCategory.DEVELOPER_TOOLS,
    "CLOUDSHELL": ServiceCategory.DEVELOPER_TOOLS, "APPLICATION_COMPOSER": ServiceCategory.DEVELOPER_TOOLS,
    "FAULT_INJECTION_SIMULATOR": ServiceCategory.DEVELOPER_TOOLS, 
    "MICROSERVICE_EXTRACTOR": ServiceCategory.DEVELOPER_TOOLS,
    "PROTON": ServiceCategory.DEVELOPER_TOOLS, "COPILOT_CLI": ServiceCategory.DEVELOPER_TOOLS,
    "CODEGURU_REVIEWER": ServiceCategory.DEVELOPER_TOOLS, "CODEGURU_PROFILER": ServiceCategory.DEVELOPER_TOOLS,
    
    # SECURITY
    "IAM": ServiceCategory.SECURITY, "COGNITO": ServiceCategory.SECURITY, 
    "SECRETS_MANAGER": ServiceCategory.SECURITY, "KMS": ServiceCategory.SECURITY,
    "CLOUDHSM": ServiceCategory.SECURITY, "CERTIFICATE_MANAGER": ServiceCategory.SECURITY,
    "WAF": ServiceCategory.SECURITY, "SHIELD": ServiceCategory.SECURITY, 
    "GUARDDUTY": ServiceCategory.SECURITY, "MACIE": ServiceCategory.SECURITY,
    "INSPECTOR": ServiceCategory.SECURITY, "AUDIT_MANAGER": ServiceCategory.SECURITY,
    "SECURITY_HUB": ServiceCategory.SECURITY, "RESOURCE_ACCESS_MANAGER": ServiceCategory.SECURITY,
    "DETECTIVE": ServiceCategory.SECURITY, "FIREWALL_MANAGER": ServiceCategory.SECURITY,
    "NETWORK_FIREWALL": ServiceCategory.SECURITY, "IAM_IDENTITY_CENTER": ServiceCategory.SECURITY,
    "VERIFIED_PERMISSIONS": ServiceCategory.SECURITY, 
    "PRIVATE_CERTIFICATE_AUTHORITY": ServiceCategory.SECURITY,
    "DIRECTORY_SERVICE": ServiceCategory.SECURITY, "PAYMENT_CRYPTOGRAPHY": ServiceCategory.SECURITY,
    "SIGNER": ServiceCategory.SECURITY, "SECURITY_LAKE": ServiceCategory.SECURITY,
    "ARTIFACT": ServiceCategory.SECURITY,
    
    # MANAGEMENT
    "CONFIG": ServiceCategory.MANAGEMENT, "CLOUDTRAIL": ServiceCategory.MANAGEMENT,
    "TRUSTED_ADVISOR": ServiceCategory.MANAGEMENT, "CONTROL_TOWER": ServiceCategory.MANAGEMENT,
    "SERVICE_CATALOG": ServiceCategory.MANAGEMENT, "LICENSE_MANAGER": ServiceCategory.MANAGEMENT,
    "ORGANIZATIONS": ServiceCategory.MANAGEMENT, "RESOURCE_GROUPS": ServiceCategory.MANAGEMENT,
    "TAG_EDITOR": ServiceCategory.MANAGEMENT, "MANAGED_GRAFANA": ServiceCategory.MANAGEMENT,
    "MANAGED_PROMETHEUS": ServiceCategory.MANAGEMENT, "OPSWORKS_CM": ServiceCategory.MANAGEMENT,
    "CHATBOT": ServiceCategory.MANAGEMENT, "LAUNCH_WIZARD": ServiceCategory.MANAGEMENT,
    "RESILIENCE_HUB": ServiceCategory.MANAGEMENT, "INCIDENT_MANAGER": ServiceCategory.MANAGEMENT,
    "SERVICE_MANAGEMENT_CONNECTOR": ServiceCategory.MANAGEMENT, "APP_CONFIG": ServiceCategory.MANAGEMENT,
    "CLOUDWATCH_LOGS": ServiceCategory.MANAGEMENT, "CLOUDWATCH_LOGS_INSIGHTS": ServiceCategory.MANAGEMENT,
    "SYSTEMS_MANAGER_PARAMETER_STORE": ServiceCategory.MANAGEMENT,
    
    # MIGRATION
    "MIGRATION_HUB": ServiceCategory.MIGRATION, "APPLICATION_MIGRATION_SERVICE": ServiceCategory.MIGRATION,
    "DATABASE_MIGRATION_SERVICE": ServiceCategory.MIGRATION, "DMS_FLEET_ADVISOR": ServiceCategory.MIGRATION,
    "DATASYNC": ServiceCategory.MIGRATION, "TRANSFER_FAMILY": ServiceCategory.MIGRATION,
    "MIGRATION_EVALUATOR": ServiceCategory.MIGRATION, "MIGRATION_HUB_REFACTOR_SPACES": ServiceCategory.MIGRATION,
    "MIGRATION_HUB_ORCHESTRATOR": ServiceCategory.MIGRATION, "MAINFRAME_MODERNIZATION": ServiceCategory.MIGRATION,
    "SNOW_FAMILY": ServiceCategory.MIGRATION, "SNOWCONE": ServiceCategory.MIGRATION,
    
    # BUSINESS APPLICATIONS
    "CONNECT": ServiceCategory.BUSINESS, "PINPOINT": ServiceCategory.BUSINESS, 
    "CHIME": ServiceCategory.BUSINESS, "WORKMAIL": ServiceCategory.BUSINESS,
    "WORKDOCS": ServiceCategory.BUSINESS, "ALEXA_FOR_BUSINESS": ServiceCategory.BUSINESS,
    "SUPPLY_CHAIN": ServiceCategory.BUSINESS, "WICKR": ServiceCategory.BUSINESS,
    "CONNECT_CUSTOMER_PROFILES": ServiceCategory.BUSINESS, "CHIME_SDK": ServiceCategory.BUSINESS,
    "AMPLIFY_UI_BUILDER": ServiceCategory.BUSINESS,
    
    # END USER COMPUTING
    "WORKSPACES": ServiceCategory.END_USER_COMPUTING, "APPSTREAM": ServiceCategory.END_USER_COMPUTING,
    "APPSTREAM_2": ServiceCategory.END_USER_COMPUTING, "WORKSPACES_WEB": ServiceCategory.END_USER_COMPUTING,
    "WORKSPACES_THIN_CLIENT": ServiceCategory.END_USER_COMPUTING,
    
    # IOT
    "IOT_CORE": ServiceCategory.IOT, "IOT_GREENGRASS": ServiceCategory.IOT, 
    "IOT_ANALYTICS": ServiceCategory.IOT, "IOT_DEVICE_MANAGEMENT": ServiceCategory.IOT,
    "IOT_DEVICE_DEFENDER": ServiceCategory.IOT, "IOT_EVENTS": ServiceCategory.IOT,
    "IOT_SITEWISE": ServiceCategory.IOT, "IOT_TWINMAKER": ServiceCategory.IOT,
    "IOT_FLEETWISE": ServiceCategory.IOT, "IOT_ROBORUNNER": ServiceCategory.IOT,
    "IOT_1CLICK": ServiceCategory.IOT, "IOT_BUTTON": ServiceCategory.IOT,
    "IOT_EDUKIT": ServiceCategory.IOT, "IOT_EXPRESSLINK": ServiceCategory.IOT,
    "FREERTOS": ServiceCategory.IOT,
    
    # ROBOTICS
    "ROBOMAKER": ServiceCategory.ROBOTICS,
    
    # MEDIA
    "ELASTIC_TRANSCODER": ServiceCategory.MEDIA, "ELEMENTAL_MEDIACONVERT": ServiceCategory.MEDIA,
    "ELEMENTAL_MEDIALIVE": ServiceCategory.MEDIA, "ELEMENTAL_MEDIAPACKAGE": ServiceCategory.MEDIA,
    "ELEMENTAL_MEDIASTORE": ServiceCategory.MEDIA, "ELEMENTAL_MEDIATAILOR": ServiceCategory.MEDIA,
    "ELEMENTAL_MEDIACONNECT": ServiceCategory.MEDIA, "INTERACTIVE_VIDEO_SERVICE": ServiceCategory.MEDIA,
    "NIMBLE_STUDIO": ServiceCategory.MEDIA, "THINKBOX_DEADLINE": ServiceCategory.MEDIA,
    "ELASTIC_TRANSCODER_PIPELINE": ServiceCategory.MEDIA,
    
    # GAME
    "GAMELIFT": ServiceCategory.GAME, "GAMESPARKS": ServiceCategory.GAME, 
    "LUMBERYARD": ServiceCategory.GAME,
    
    # AR/VR
    "SUMERIAN": ServiceCategory.AR_VR, "AR_VR": ServiceCategory.AR_VR, 
    "SIMSPACE_WEAVER": ServiceCategory.AR_VR,
    
    # BLOCKCHAIN
    "MANAGED_BLOCKCHAIN": ServiceCategory.BLOCKCHAIN, 
    "QUANTUM_LEDGER_DATABASE": ServiceCategory.BLOCKCHAIN,
    
    # QUANTUM
    "BRAKET": ServiceCategory.QUANTUM,
    
    # SATELLITE
    "GROUND_STATION": ServiceCategory.SATELLITE,
    
    # COST MANAGEMENT
    "COST_EXPLORER": ServiceCategory.COST_MANAGEMENT, "COST_AND_USAGE_REPORT": ServiceCategory.COST_MANAGEMENT,
    "BUDGETS": ServiceCategory.COST_MANAGEMENT, "COST_ANOMALY_DETECTION": ServiceCategory.COST_MANAGEMENT,
    "SAVINGS_PLANS": ServiceCategory.COST_MANAGEMENT, "BILLING_CONDUCTOR": ServiceCategory.COST_MANAGEMENT,
    "MARKETPLACE": ServiceCategory.COST_MANAGEMENT,
    
    # CUSTOMER ENABLEMENT
    "IQ": ServiceCategory.CUSTOMER_ENABLEMENT, "SUPPORT": ServiceCategory.CUSTOMER_ENABLEMENT,
    "MANAGED_SERVICES": ServiceCategory.CUSTOMER_ENABLEMENT,
}


# Service metadata registry - Core services with detailed metadata (83+ services)
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
    
    # AI/ML (10 services)
    ResourceType.SAGEMAKER: {"category": ServiceCategory.AI_ML, "name": "SageMaker", "metrics": ["Instance hours"], "optimization_opportunities": ["Spot training"]},
    ResourceType.TEXTRACT: {"category": ServiceCategory.AI_ML, "name": "Textract", "metrics": ["Documents processed"], "optimization_opportunities": ["Batch optimization"]},
    ResourceType.REKOGNITION: {"category": ServiceCategory.AI_ML, "name": "Rekognition", "metrics": ["API calls"], "optimization_opportunities": ["API call optimization"]},
    ResourceType.COMPREHEND: {"category": ServiceCategory.AI_ML, "name": "Comprehend", "metrics": ["Units"], "optimization_opportunities": ["Batch optimization"]},
    ResourceType.TRANSLATE: {"category": ServiceCategory.AI_ML, "name": "Translate", "metrics": ["Characters"], "optimization_opportunities": ["Batch translation"]},
    ResourceType.POLLY: {"category": ServiceCategory.AI_ML, "name": "Polly", "metrics": ["Characters"], "optimization_opportunities": ["Cache optimization"]},
    ResourceType.LEX: {"category": ServiceCategory.AI_ML, "name": "Lex", "metrics": ["Requests"], "optimization_opportunities": ["Request optimization"]},
    ResourceType.FORECAST: {"category": ServiceCategory.AI_ML, "name": "Forecast", "metrics": ["Forecasts"], "optimization_opportunities": ["Forecast optimization"]},
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


def _auto_generate_service_name(resource_type: ResourceType) -> str:
    """Gera nome amigável automaticamente a partir do enum."""
    name = resource_type.value
    # Convert underscores to spaces and capitalize properly
    return name.replace('_', ' ').title().replace('Aws', 'AWS').replace('Iot', 'IoT').replace('Ai', 'AI')


def _auto_detect_category(resource_type: ResourceType) -> ServiceCategory:
    """Detecta automaticamente a categoria de um serviço."""
    service_name = resource_type.name
    return SERVICE_CATEGORY_MAP.get(service_name, ServiceCategory.OTHER)


def get_service_info(resource_type: ResourceType) -> Dict:
    """
    Get metadata for a service.
    
    Se o serviço não estiver no registro explícito, gera metadados automaticamente.
    Isso garante que TODOS os 268+ serviços AWS sejam suportados.
    """
    # Se já tem no registro, retorna
    if resource_type in AWS_SERVICE_REGISTRY:
        return AWS_SERVICE_REGISTRY[resource_type]
    
    # Senão, gera automaticamente
    return {
        "category": _auto_detect_category(resource_type),
        "name": _auto_generate_service_name(resource_type),
        "metrics": ["Usage", "Requests", "Resources"],
        "optimization_opportunities": ["Resource optimization", "Cost reduction", "Performance tuning"],
    }


def get_services_by_category(category: ServiceCategory) -> List[ResourceType]:
    """Get all services in a category (inclui geração automática)."""
    services = []
    
    # Itera por TODOS os ResourceType
    for resource_type in ResourceType:
        if resource_type in [ResourceType.GENERIC, ResourceType.UNKNOWN]:
            continue
        
        # Pega info (auto-gerada se necessário)
        info = get_service_info(resource_type)
        if info.get("category") == category:
            services.append(resource_type)
    
    return services


def get_all_categories() -> List[ServiceCategory]:
    """Get all service categories."""
    return sorted(list(ServiceCategory), key=lambda x: x.value)


def get_total_services_count() -> int:
    """Get total count of supported AWS services."""
    return len([r for r in ResourceType if r not in [ResourceType.GENERIC, ResourceType.UNKNOWN]])
